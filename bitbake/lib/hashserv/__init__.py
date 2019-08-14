# Copyright (C) 2018-2019 Garmin Ltd.
#
# SPDX-License-Identifier: GPL-2.0-only
#

from http.server import BaseHTTPRequestHandler, HTTPServer
import contextlib
import urllib.parse
import sqlite3
import json
import traceback
import logging
import socketserver
import queue
import threading
import signal
import time
import math
import socket
from datetime import datetime

logger = logging.getLogger('hashserv')

class Stats(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.num = 0
        self.total_time = 0
        self.max_time = 0
        self.m = 0
        self.s = 0

    def update(self, start_time):
        elapsed = time.perf_counter() - start_time

        self.num += 1
        if self.num == 1:
            self.m = elapsed
            self.s = 0
        else:
            last_m = self.m
            self.m = last_m + (elapsed - last_m) / self.num
            self.s = self.s + (elapsed - last_m) * (elapsed - self.m)

        self.total_time += elapsed

        if self.max_time < elapsed:
            self.max_time = elapsed

    @property
    def average(self):
        if self.num == 0:
            return 0
        return self.total_time / self.num

    @property
    def stdev(self):
        if self.num <= 1:
            return 0
        return math.sqrt(self.s / (self.num - 1))

    def todict(self):
        return {k: getattr(self, k) for k in ('num', 'total_time', 'max_time', 'average', 'stdev')}

request_stats = Stats()
connect_stats = Stats()

class HashEquivalenceServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.equivalent_path = self.prefix + '/v1/equivalent'
        self.stats_path = self.prefix + '/v1/stats'

    def setup(self):
        global connect_stats

        if self.request.connect_time is not None:
            connect_stats.update(self.request.connect_time)
            self.request.connect_time = None

        self.start_time = time.perf_counter()
        super().setup()

    def finish(self):
        global request_stats

        super().finish()
        request_stats.update(self.start_time)

    def log_message(self, f, *args):
        logger.debug(f, *args)

    def opendb(self):
        self.db = sqlite3.connect(self.dbname)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA synchronous = OFF;")
        self.db.execute("PRAGMA journal_mode = MEMORY;")

    def do_GET_equivalent(self, p):
        query = urllib.parse.parse_qs(p.query, strict_parsing=True)
        method = query['method'][0]
        taskhash = query['taskhash'][0]

        d = None
        with contextlib.closing(self.db.cursor()) as cursor:
            cursor.execute('SELECT taskhash, method, unihash FROM tasks_v2 WHERE method=:method AND taskhash=:taskhash ORDER BY created ASC LIMIT 1',
                    {'method': method, 'taskhash': taskhash})

            row = cursor.fetchone()

            if row is not None:
                logger.debug('Found equivalent task %s', row['taskhash'])
                d = {k: row[k] for k in ('taskhash', 'method', 'unihash')}

        data = json.dumps(d).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET_stats(self, p):
        global request_stats
        global connect_stats
        d = {
            'requests': request_stats.todict(),
            'connections': connect_stats.todict()
            }

        data = json.dumps(d).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_DELETE_stats(self, p):
        global request_stats
        global connect_stats

        request_stats.reset()
        connect_stats.reset()

        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        try:
            if not self.db:
                self.opendb()

            p = urllib.parse.urlparse(self.path)

            if p.path == self.prefix + '/v1/equivalent':
                self.do_GET_equivalent(p)
            elif p.path == self.prefix + '/v1/stats':
                self.do_GET_stats(p)
            else:
                self.send_error(404)
                return
        except:
            logger.exception('Error in GET')
            self.send_error(400, explain=traceback.format_exc())

    def do_POST(self):
        try:
            if not self.db:
                self.opendb()

            p = urllib.parse.urlparse(self.path)

            if p.path != self.prefix + '/v1/equivalent':
                self.send_error(404)
                return

            length = int(self.headers['content-length'])
            data = json.loads(self.rfile.read(length).decode('utf-8'))

            with contextlib.closing(self.db.cursor()) as cursor:
                cursor.execute('''
                    -- Find tasks with a matching outhash (that is, tasks that
                    -- are equivalent)
                    SELECT taskhash, method, unihash FROM tasks_v2 WHERE method=:method AND outhash=:outhash

                    -- If there is an exact match on the taskhash, return it.
                    -- Otherwise return the oldest matching outhash of any
                    -- taskhash
                    ORDER BY CASE WHEN taskhash=:taskhash THEN 1 ELSE 2 END,
                        created ASC

                    -- Only return one row
                    LIMIT 1
                    ''', {k: data[k] for k in ('method', 'outhash', 'taskhash')})

                row = cursor.fetchone()

                # If no matching outhash was found, or one *was* found but it
                # wasn't an exact match on the taskhash, a new entry for this
                # taskhash should be added
                if row is None or row['taskhash'] != data['taskhash']:
                    # If a row matching the outhash was found, the unihash for
                    # the new taskhash should be the same as that one.
                    # Otherwise the caller provided unihash is used.
                    unihash = data['unihash']
                    if row is not None:
                        unihash = row['unihash']

                    insert_data = {
                            'method': data['method'],
                            'outhash': data['outhash'],
                            'taskhash': data['taskhash'],
                            'unihash': unihash,
                            'created': datetime.now()
                            }

                    for k in ('owner', 'PN', 'PV', 'PR', 'task', 'outhash_siginfo'):
                        if k in data:
                            insert_data[k] = data[k]

                    cursor.execute('''INSERT INTO tasks_v2 (%s) VALUES (%s)''' % (
                            ', '.join(sorted(insert_data.keys())),
                            ', '.join(':' + k for k in sorted(insert_data.keys()))),
                        insert_data)

                    logger.info('Adding taskhash %s with unihash %s', data['taskhash'], unihash)

                    self.db.commit()
                    d = {'taskhash': data['taskhash'], 'method': data['method'], 'unihash': unihash}
                else:
                    d = {k: row[k] for k in ('taskhash', 'method', 'unihash')}

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(d).encode('utf-8'))
        except:
            logger.exception('Error in POST')
            self.send_error(400, explain=traceback.format_exc())

    def do_DELETE(self):
        try:
            p = urllib.parse.urlparse(self.path)

            if p.path == self.prefix + '/v1/stats':
                self.do_DELETE_stats(p)
            else:
                self.send_error(404)
                return
        except:
            logger.exception('Error in DELETE')
            self.send_error(400, explain=traceback.format_exc())

class ClientSocket(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect_time = time.perf_counter()

    @classmethod
    def create(cls, sock):
        import _socket
        fd = _socket.dup(sock.fileno())
        s = cls(sock.family, sock.type, sock.proto, fileno=fd)
        s.settimeout(sock.gettimeout())
        return s

class ThreadedHTTPServer(HTTPServer):
    quit = False

    def serve_forever(self):
        self.requestqueue = queue.Queue()
        self.handlerthread = threading.Thread(target=self.process_request_thread)
        self.handlerthread.daemon = False

        self.handlerthread.start()

        signal.signal(signal.SIGTERM, self.sigterm_exception)
        super().serve_forever()
        os._exit(0)

    def sigterm_exception(self, signum, stackframe):
        self.server_close()
        os._exit(0)

    def process_request_thread(self):
        while not self.quit:
            try:
                (request, client_address) = self.requestqueue.get(True)
            except queue.Empty:
                continue
            if request is None:
                continue
            try:
                self.finish_request(request, client_address)
            except Exception:
                self.handle_error(request, client_address)
            finally:
                self.shutdown_request(request)
        os._exit(0)

    def process_request(self, request, client_address):
        self.requestqueue.put((request, client_address))

    def server_close(self):
        super().server_close()
        self.quit = True
        self.requestqueue.put((None, None))
        self.handlerthread.join()

    def get_request(self):
        sock, client_address = super().get_request()
        return ClientSocket.create(sock), client_address

def create_server(addr, dbname, prefix=''):
    class Handler(HashEquivalenceServer):
        pass

    db = sqlite3.connect(dbname)
    db.row_factory = sqlite3.Row

    Handler.prefix = prefix
    Handler.db = None
    Handler.dbname = dbname

    with contextlib.closing(db.cursor()) as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                outhash TEXT NOT NULL,
                taskhash TEXT NOT NULL,
                unihash TEXT NOT NULL,
                created DATETIME,

                -- Optional fields
                owner TEXT,
                PN TEXT,
                PV TEXT,
                PR TEXT,
                task TEXT,
                outhash_siginfo TEXT,

                UNIQUE(method, outhash, taskhash)
                )
            ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS taskhash_lookup ON tasks_v2 (method, taskhash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS outhash_lookup ON tasks_v2 (method, outhash)')

    ret = ThreadedHTTPServer(addr, Handler)

    logger.info('Starting server on %s\n', ret.server_port)

    return ret
