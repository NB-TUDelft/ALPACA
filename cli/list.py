from cli.tools.cache import get_cache_folder
from cli.tools.pico import list_entries, DeviceEntry
import typer

def get_type(entry: DeviceEntry):
  for path in get_cache_folder().glob("*_cache"):
    name = path.name[:-len("_cache")]

    if (entry["usb"].serial_number or "-") in path.read_text():
      return name.capitalize()
    
  return "-"


def list_devices():
    entries = list_entries()

    if not entries:
      typer.echo("No connected Picos found.")
      raise typer.Exit()

    rows = [
      (serial_number, entry["usb"].to_port(), get_type(entry))
      for serial_number, entry in sorted(entries.items())
    ]

    headers = ("Serial Number", "Port", "Type")
    widths = [len(headers[0]), len(headers[1]), len(headers[2])]

    for entry, port, type in rows:
      widths[0] = max(widths[0], len(entry))
      widths[1] = max(widths[1], len(port))
      widths[2] = max(widths[1], len(type))

    separator = f"+-{'-' * widths[0]}-+-{'-' * widths[1]}-+-{'-' * widths[2]}-+"
    output = [separator]
    output.append(f"| {headers[0]:<{widths[0]}} | {headers[1]:<{widths[1]}} | {headers[2]:<{widths[2]}} |")
    output.append(separator)

    for entry, port, type in rows:
      output.append(f"| {entry:<{widths[0]}} | {port:<{widths[1]}} | {type:<{widths[2]}} |")

    output.append(separator)

    typer.echo("\n".join(output))
