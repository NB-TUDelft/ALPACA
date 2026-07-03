from bus import link
from command import SET_PIN
from machine import Pin

@link.register(SET_PIN)
def set_pin_cmd(pin_number, value):
  Pin(pin_number, Pin.OUT).value(value)