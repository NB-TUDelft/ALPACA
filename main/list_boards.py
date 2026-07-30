from belay import list_devices

def list_boards():
  return list(filter(lambda x: x.serial_number, list_devices()))