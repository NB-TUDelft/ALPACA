from typing import Literal, TypedDict

from belay import list_devices, Device, UsbSpecifier
import typer

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

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl

def select_with_hover(choices, title="", on_highlight=None):
    idx = [0]

    def render():
        lines = []
        if title:
            lines.append(("bold", title + "\n"))
        for i, c in enumerate(choices):
            style = "reverse" if i == idx[0] else ""
            prefix = "> " if i == idx[0] else "  "
            lines.append((style, f"{prefix}{c}\n"))
        return lines

    def fire():
        if on_highlight is not None:
            on_highlight(choices[idx[0]])

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _(e):
        idx[0] = (idx[0] - 1) % len(choices); fire()

    @kb.add("down")
    @kb.add("j")
    def _(e):
        idx[0] = (idx[0] + 1) % len(choices); fire()

    @kb.add("enter")
    def _(e):
        e.app.exit(result=idx[0])

    @kb.add("c-c")
    @kb.add("escape")
    def _(e):
        e.app.exit(result=None)

    ctrl = FormattedTextControl(render, focusable=True, show_cursor=False)
    app = Application(layout=Layout(HSplit([Window(ctrl)])), key_bindings=kb, erase_when_done=True)

    fire()
    return app.run()

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

  selection = select_with_hover(
    title=f"Select a {name.capitalize()} Pico",
    choices=choices,
    on_highlight=on_hover
  )

  for entry in entries.values():
    entry["board"]("led.value(0)")
    # entry["board"].soft_reset()

  if choices[selection] == "None":
    return
  else:
    return entries[choices[selection]]


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

  if typer.confirm("Remember your selection?", default=True):
    with open(cache_file, "a") as file:
      file.write(f"\n{entry['usb'].serial_number}")

  return entry
  