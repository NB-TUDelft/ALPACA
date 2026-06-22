"""Coordination between `alpaca connect` (holds a board's serial port open in
an mpremote REPL) and `alpaca sync` (needs that same port).

`connect` registers its PID and parks an mpremote REPL in a supervised loop.
`sync` calls pause_connect() before touching any device: it signals the live
connect process to drop the port, waits for it to free, syncs, then
resume_connect() lets the parked loop reconnect on its own.
"""

import os
import signal
import time
from pathlib import Path

from cli.tools.cache import get_cache_folder

PAUSE_SIGNAL = signal.SIGUSR1

def _lock_file() -> Path:
  return get_cache_folder() / "connect.lock"

def _busy_file() -> Path:
  return get_cache_folder() / "sync.busy"

def register_connect() -> None:
  _lock_file().write_text(str(os.getpid()))


def unregister_connect() -> None:
  lock = _lock_file()

  if lock.exists() and lock.read_text().strip() == str(os.getpid()):
    lock.unlink()


def _live_connect_pid() -> int | None:
  lock = _lock_file()

  if not lock.exists():
    return None

  try:
    pid = int(lock.read_text().strip())
  except ValueError:
    lock.unlink(missing_ok=True)
    return None

  try:
    os.kill(pid, 0)
  except OSError:
    lock.unlink(missing_ok=True)
    return None

  return pid


def sync_pending() -> bool:
  return _busy_file().exists()


def pause_connect() -> int | None:
  pid = _live_connect_pid()

  if pid is None:
    return None

  _busy_file().write_text("1")
  os.kill(pid, PAUSE_SIGNAL)

  time.sleep(1.0)

  return pid


def resume_connect(pid: int | None) -> None:
  """Clear the pause flag so a parked connect session reconnects."""
  _busy_file().unlink(missing_ok=True)
