# Copyright (C) 2019 Garmin Ltd.
#
# SPDX-License-Identifier: GPL-2.0-only
#

import logging
import socket
import asyncio
import bb.asyncrpc
import json
from . import create_async_client


logger = logging.getLogger("hashserv.client")


class Batch(object):
    def __init__(self):
        self.done = False
        self.cond = asyncio.Condition()
        self.pending = []
        self.results = []
        self.sent_count = 0

    async def recv(self, socket):
        while True:
            async with self.cond:
                await self.cond.wait_for(lambda: self.pending or self.done)

                if not self.pending:
                    if self.done:
                        return
                    continue

            r = await socket.recv()
            self.results.append(r)

            async with self.cond:
                self.pending.pop(0)

    async def send(self, socket, msgs):
        try:
            # In the event of a restart due to a reconnect, all in-flight
            # messages need to be resent first to keep to result count in sync
            for m in self.pending:
                await socket.send(m)

            for m in msgs:
                await socket.send(m)

                async with self.cond:
                    self.pending.append(m)
                    self.cond.notify()
                    self.sent_count += 1
        finally:
            async with self.cond:
                self.done = True
                self.cond.notify()

    async def process(self, socket, msgs):
        await asyncio.gather(
            self.recv(socket),
            self.send(socket, msgs),
        )

        if len(self.results) != self.sent_count:
            raise ValueError(
                f"Expected result count {len(self.results)}. Expected {self.sent_count}"
            )

        return self.results


class AsyncClient(bb.asyncrpc.AsyncClient):
    MODE_NORMAL = 0
    MODE_GET_STREAM = 1
    MODE_EXIST_STREAM = 2

    def __init__(self, username=None, password=None):
        super().__init__("OEHASHEQUIV", "1.1", logger)
        self.mode = self.MODE_NORMAL
        self.username = username
        self.password = password
        self.saved_become_user = None

    async def setup_connection(self):
        await super().setup_connection()
        self.mode = self.MODE_NORMAL
        if self.username:
            # Save off become user temporarily because auth() resets it
            become = self.saved_become_user
            await self.auth(self.username, self.password)

            if become:
                await self.become_user(become)

    async def send_stream_batch(self, mode, msgs):
        """
        Does a "batch" process of stream messages. This sends the query
        messages as fast as possible, and simultaneously attempts to read the
        messages back. This helps to mitigate the effects of latency to the
        hash equivalence server be allowing multiple queries to be "in-flight"
        at once

        The implementation does more complicated tracking using a count of sent
        messages so that `msgs` can be a generator function (i.e. its length is
        unknown)

        """

        b = Batch()

        async def proc():
            nonlocal b

            await self._set_mode(mode)
            return await b.process(self.socket, msgs)

        return await self._send_wrapper(proc)

    async def invoke(self, *args, **kwargs):
        # It's OK if connection errors cause a failure here, because the mode
        # is also reset to normal on a new connection
        await self._set_mode(self.MODE_NORMAL)
        return await super().invoke(*args, **kwargs)

    async def _set_mode(self, new_mode):
        async def stream_to_normal():
            await self.socket.send("END")
            return await self.socket.recv()

        async def normal_to_stream(command):
            r = await self.invoke({command: None})
            if r != "ok":
                raise ConnectionError(
                    f"Unable to transition to stream mode: Bad response from server {r!r}"
                )

            self.logger.debug("Mode is now %s", command)

        if new_mode == self.mode:
            return

        self.logger.debug("Transitioning mode %s -> %s", self.mode, new_mode)

        # Always transition to normal mode before switching to any other mode
        if self.mode != self.MODE_NORMAL:
            r = await self._send_wrapper(stream_to_normal)
            if r != "ok":
                self.check_invoke_error(r)
                raise ConnectionError(
                    f"Unable to transition to normal mode: Bad response from server {r!r}"
                )
            self.logger.debug("Mode is now normal")

        if new_mode == self.MODE_GET_STREAM:
            await normal_to_stream("get-stream")
        elif new_mode == self.MODE_EXIST_STREAM:
            await normal_to_stream("exists-stream")
        elif new_mode != self.MODE_NORMAL:
            raise Exception("Undefined mode transition {self.mode!r} -> {new_mode!r}")

        self.mode = new_mode

    async def get_unihash(self, method, taskhash):
        r = await self.get_unihash_batch([(method, taskhash)])
        return r[0]

    async def get_unihash_batch(self, args):
        result = await self.send_stream_batch(
            self.MODE_GET_STREAM,
            (f"{method} {taskhash}" for method, taskhash in args),
        )
        return [r if r else None for r in result]

    async def report_unihash(self, taskhash, method, outhash, unihash, extra={}):
        m = extra.copy()
        m["taskhash"] = taskhash
        m["method"] = method
        m["outhash"] = outhash
        m["unihash"] = unihash
        return await self.invoke({"report": m})

    async def report_unihash_equiv(self, taskhash, method, unihash, extra={}):
        m = extra.copy()
        m["taskhash"] = taskhash
        m["method"] = method
        m["unihash"] = unihash
        return await self.invoke({"report-equiv": m})

    async def get_taskhash(self, method, taskhash, all_properties=False):
        return await self.invoke(
            {"get": {"taskhash": taskhash, "method": method, "all": all_properties}}
        )

    async def unihash_exists(self, unihash):
        r = await self.unihash_exists_batch([unihash])
        return r[0]

    async def unihash_exists_batch(self, unihashes):
        result = await self.send_stream_batch(self.MODE_EXIST_STREAM, unihashes)
        return [r == "true" for r in result]

    async def get_outhash(self, method, outhash, taskhash, with_unihash=True):
        return await self.invoke(
            {
                "get-outhash": {
                    "outhash": outhash,
                    "taskhash": taskhash,
                    "method": method,
                    "with_unihash": with_unihash,
                }
            }
        )

    async def get_stats(self):
        return await self.invoke({"get-stats": None})

    async def reset_stats(self):
        return await self.invoke({"reset-stats": None})

    async def backfill_wait(self):
        return (await self.invoke({"backfill-wait": None}))["tasks"]

    async def remove(self, where):
        return await self.invoke({"remove": {"where": where}})

    async def clean_unused(self, max_age):
        return await self.invoke({"clean-unused": {"max_age_seconds": max_age}})

    async def auth(self, username, token):
        result = await self.invoke({"auth": {"username": username, "token": token}})
        self.username = username
        self.password = token
        self.saved_become_user = None
        return result

    async def refresh_token(self, username=None):
        m = {}
        if username:
            m["username"] = username
        result = await self.invoke({"refresh-token": m})
        if (
            self.username
            and not self.saved_become_user
            and result["username"] == self.username
        ):
            self.password = result["token"]
        return result

    async def set_user_perms(self, username, permissions):
        return await self.invoke(
            {"set-user-perms": {"username": username, "permissions": permissions}}
        )

    async def get_user(self, username=None):
        m = {}
        if username:
            m["username"] = username
        return await self.invoke({"get-user": m})

    async def get_all_users(self):
        return (await self.invoke({"get-all-users": {}}))["users"]

    async def new_user(self, username, permissions):
        return await self.invoke(
            {"new-user": {"username": username, "permissions": permissions}}
        )

    async def delete_user(self, username):
        return await self.invoke({"delete-user": {"username": username}})

    async def become_user(self, username):
        result = await self.invoke({"become-user": {"username": username}})
        if username == self.username:
            self.saved_become_user = None
        else:
            self.saved_become_user = username
        return result

    async def get_db_usage(self):
        return (await self.invoke({"get-db-usage": {}}))["usage"]

    async def get_db_query_columns(self):
        return (await self.invoke({"get-db-query-columns": {}}))["columns"]

    async def gc_status(self):
        return await self.invoke({"gc-status": {}})

    async def gc_mark(self, mark, where):
        """
        Starts a new garbage collection operation identified by "mark". If
        garbage collection is already in progress with "mark", the collection
        is continued.

        All unihash entries that match the "where" clause are marked to be
        kept. In addition, any new entries added to the database after this
        command will be automatically marked with "mark"
        """
        return await self.invoke({"gc-mark": {"mark": mark, "where": where}})

    async def gc_sweep(self, mark):
        """
        Finishes garbage collection for "mark". All unihash entries that have
        not been marked will be deleted.

        It is recommended to clean unused outhash entries after running this to
        cleanup any dangling outhashes
        """
        return await self.invoke({"gc-sweep": {"mark": mark}})


class Client(bb.asyncrpc.Client):
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

        super().__init__()
        self._add_methods(
            "connect_tcp",
            "connect_websocket",
            "get_unihash",
            "get_unihash_batch",
            "report_unihash",
            "report_unihash_equiv",
            "get_taskhash",
            "unihash_exists",
            "unihash_exists_batch",
            "get_outhash",
            "get_stats",
            "reset_stats",
            "backfill_wait",
            "remove",
            "clean_unused",
            "auth",
            "refresh_token",
            "set_user_perms",
            "get_user",
            "get_all_users",
            "new_user",
            "delete_user",
            "become_user",
            "get_db_usage",
            "get_db_query_columns",
            "gc_status",
            "gc_mark",
            "gc_sweep",
        )

    def _get_async_client(self):
        return AsyncClient(self.username, self.password)


class ClientPool(bb.asyncrpc.ClientPool):
    def __init__(
        self,
        address,
        max_clients,
        *,
        username=None,
        password=None,
        become=None,
    ):
        super().__init__(max_clients)
        self.address = address
        self.username = username
        self.password = password
        self.become = become

    async def _new_client(self):
        client = await create_async_client(
            self.address,
            username=self.username,
            password=self.password,
        )
        if self.become:
            await client.become_user(self.become)
        return client

    def _run_key_tasks(self, queries, call):
        keys = list(queries.keys())
        results = {}

        async def task(client):
            client_keys = []

            def get_next():
                nonlocal client_keys
                nonlocal keys

                if not keys:
                    return

                k = keys.pop()
                client_keys.append(k)

                yield queries[k]

            r = await call(client, get_next())

            for idx, k in enumerate(client_keys):
                results[k] = r[idx]

        self.run_tasks(task for _ in range(self.max_clients))
        return results

    def get_unihashes(self, queries):
        """
        Query multiple unihashes in parallel.

        The queries argument is a dictionary with arbitrary key. The values
        must be a tuple of (method, taskhash).

        Returns a dictionary with a corresponding key for each input key, and
        the value is the queried unihash (which might be none if the query
        failed)
        """

        async def call(client, gen):
            return await client.get_unihash_batch(gen)

        return self._run_key_tasks(queries, call)

    def unihashes_exist(self, queries):
        """
        Query multiple unihash existence checks in parallel.

        The queries argument is a dictionary with arbitrary key. The values
        must be a unihash.

        Returns a dictionary with a corresponding key for each input key, and
        the value is True or False if the unihash is known by the server (or
        None if there was a failure)
        """

        async def call(client, gen):
            return await client.unihash_exists_batch(gen)

        return self._run_key_tasks(queries, call)
