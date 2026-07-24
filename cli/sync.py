from typing import Annotated

import typer

from cli.tools.cache import collect_files, get_cache_folder, PROJECT_ROOT
from cli.tools.pico import get_pico
from rich.progress import Progress
from cli.connect import connect as connect_cmd
import os
import signal
import shutil
import time
import importlib.metadata

def sync(
  connect: Annotated[str, typer.Option(help="Connect to an pico after syncing")] = ""
):  
  choices = []

  for pico_name in ["student", "helper"]:
    entry = get_pico(pico_name)
  
    if not entry:
      print(f"No {pico_name} picos present")
      continue

    device = entry["board"]

    # Prepare the root
    src = collect_files(pico_name)

    # Move the root to pico
    with Progress() as progress:
      task_id = progress.add_task("")

      def progress_update(description=None, **kwargs):
        return progress.update(task_id, description=description, **kwargs)

      device.sync(src, progress_update=progress_update)
      progress_update(description=f"{pico_name.capitalize()} Complete.")

      choices.append(device)

      progress.stop()

  for device in choices:
    device.soft_reset()
  
  if connect != "":
    entry_to_connect = get_pico(connect)

    if not entry_to_connect:
      print(f"No {connect} picos present")
      return
      
    connect_cmd(connect)

