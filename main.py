# pyright: reportMissingModuleSource=false

from belay import Device, list_devices

pico = Device("/dev/cu.usbmodem1401")

@pico.task
def annen():
  from helper import link
  from command import SET_PIN

  link.call(SET_PIN, 9, True)


annen()