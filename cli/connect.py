import os
import signal
import subprocess
import sys
import signal
from typing import Annotated

import typer

from cli.tools.cache import get_cache_folder
from cli.tools.pico import get_pico


def connect(pico_name: Annotated[str, typer.Argument(help="Pico to connect i.e. student, helper...")]):
  entry = get_pico(pico_name)

  if not entry: return

  entry["board"].close()

  port = entry["usb"].to_port()
  
  subprocess.run(
    [sys.executable, "-m", "mpremote", "connect", f"port:{port}", "repl"],
  )

#   signal.signal(signal.SIGTERM, signal_handler(child))

# def signal_handler(child: subprocess.Popen):
#   def _signal_handler(signum, frame):
#     child.kill()

#   return _signal_handler
