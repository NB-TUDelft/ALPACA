from typing import Literal, TypedDict, cast

from belay import list_devices, Device, UsbSpecifier
from simple_term_menu import TerminalMenu
from pathlib import Path
import os

from cli.tools.cache import get_cache_folder

class DeviceEntry(TypedDict):
  usb: UsbSpecifier
  board: Device

entries_cache: dict[str, DeviceEntry] | None = None

def list_entries() -> dict[str, DeviceEntry]:
  global entries_cache

  if entries_cache: return entries_cache

  usb_devices = list_devices()
  
  entries: dict[str, DeviceEntry] = {}

  for usb in usb_devices:
    device = Device(usb.to_port())

    if not usb.serial_number: continue

    entries[usb.serial_number] = DeviceEntry(
      usb=usb,
      board=device
    )

  entries_cache = entries

  return entries

def ask_device(name: str = "") -> DeviceEntry | None:

  choices: list[str] = []

  entries = list_entries()

  if len(entries) == 0:
    return

  for (serial_number, entry) in entries.items():
    choices.append(serial_number)

    entry["board"]("from machine import Pin")
    entry["board"]("led = Pin(25, Pin.OUT)")

  def on_hover(item):
    for serial, device in entries.items():
      device["board"](f"led.value({ 1 if serial == item else 0 })")

    return "Selected board's LED is turned on"

  choices.append("None")

  menu = TerminalMenu(
    choices,
    preview_command=on_hover,
    preview_size=0.25,
    title=f"Select a {name.capitalize()} Pico"
  )

  choice = cast(int, menu.show())

  for entry in entries.values():
    entry["board"]("led.value(0)")
    # entry["board"].soft_reset()

  if choices[choice] == "None":
    return
  else:
    return entries[choices[choice]]


def get_pico(name: Literal["student", "helper"] | str) -> DeviceEntry | None:
  global entries_cache

  if entries_cache:
    entries = entries_cache
  else:
    entries_cache = list_entries()

    entries = entries_cache

  # Remember from cache
  cache_file = get_cache_folder() / f"{name}_cache"

  if cache_file.exists():
    cache = cache_file.read_text().splitlines()
    
    for serial_number in cache:
      if serial_number in entries:
        return entries[serial_number]

  # If none in cache ask
  entry = ask_device(name)

  if not entry: return None

  if TerminalMenu(["Yes", "No"], title="Remember your selection?").show() == 0:
    with open(cache_file, "a") as file:
      file.write(f"\n{entry['usb'].serial_number}")

  return entry
  