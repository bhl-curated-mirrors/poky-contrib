#!/usr/bin/env python3

from pathlib import Path
from threading import Event
import argparse
import os
import shutil
import signal

resumed = Event()
runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/run")

def signal_handler(signum, _frame):
    """Wait for an external signal to exit the process gracefully."""
    resumed.set()


def main(path, user, group, mode, jobs):
    """Setup a fifo to use as jobserver shared between builds."""
    try:
        path.unlink(missing_ok=True)
        os.mkfifo(path)
        shutil.chown(path, user, group)
        os.chmod(path, mode)
    except (FileNotFoundError, PermissionError) as exc:
        raise SystemExit(f"failed to create fifo: {path}: {exc.strerror}")

    print(f"jobserver: {path}: {jobs} jobs")
    fifo = os.open(path, os.O_RDWR)
    os.write(fifo, b"+" * jobs)

    print("jobserver: ready; waiting indefinitely")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    resumed.wait()

    print("jobserver: exiting")
    path.unlink()
    os.close(fifo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Make jobserver',
        description='Simple application to instantiate a jobserver fifo and hang around',
    )
    parser.add_argument(
        "--mode",
        help="Permission to apply to jobserver fifo",
        type=lambda v: int(v, 8),
        default=0o0666,
    )
    parser.add_argument(
        "--user",
        help="Username or id to assign ownership of fifo to",
        default=os.getuid(),
    )
    parser.add_argument(
        "--group",
        help="Groupname or id to assign ownership of fifo to",
        default=os.getgid(),
    )
    parser.add_argument(
        "path",
        help="Path to jobserver fifo",
        type=Path,
        nargs='?',
        default=f"{runtime_dir}/jobserver",
    )
    parser.add_argument(
        "jobs",
        help="Number of tokens to load jobserver with",
        type=int,
        nargs='?',
        default=os.cpu_count(),
    )
    args = parser.parse_args()
    main(args.path, args.user, args.group, args.mode, args.jobs)
