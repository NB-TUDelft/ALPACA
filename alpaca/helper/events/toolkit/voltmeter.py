from machine import Pin, ADC
from time import ticks_ms, ticks_diff
from display import display

from bus import link

_ADC0_PICO_PIN = const(26)
_ADC0_RANGE = const(30 / 2**16)

adc0 = ADC(_ADC0_PICO_PIN)

_VOLTAGE_FPS = const(2)
_VOLTAGE_PERIOD_MS = const(1000 // _VOLTAGE_FPS)

def display_voltage(last_tick):
  value = adc0.read_u16() * _ADC0_RANGE

  # VOM Polarity Pin GP26 is also connected to DB7
  # of the LCD display 
  if display.driver.data[3].value() == 1:
    display.set_text(f"+{value:.2f}V")
  else:
    display.set_text(f"-{value:.2f}V")
