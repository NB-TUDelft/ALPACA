from utime import ticks_diff, ticks_ms
import micropython
from machine import Pin
from display.driver import HD44780

_VOLTAGE_REFRESH_RATE = const(4) # Hz
_VOLTAGE_PERIOD_MS = const(1000 // _VOLTAGE_REFRESH_RATE)
_COLS = const(8)

class LCDManager():
  def __init__(self) -> None:
    self.driver = HD44780(17, 18, [19, 20, 21, 22])

    self.text = ["", ""]
    self.overlay = [None, None]
    self.shown = ["", ""]  # what the display currently holds, padded to _COLS
    self.update = False

  def draw(self, last_tick):
    if not self.update:
      return True

    if ticks_diff(ticks_ms(), last_tick) < _VOLTAGE_PERIOD_MS:
      return True

    self.update = False

    lines = [
      ((self.overlay[row] or self.text[row]) + " " * _COLS)[:_COLS]
      for row in range(2)
    ]

    if lines == self.shown:
      return

    # VOM Polarity Pin GP26 is also connected to DB7
    # of the LCD display, so set it to output when
    # sending data to the display
    self.driver.data[3].init(Pin.OUT)

    for row in range(2):
      if lines[row] != self.shown[row]:
        self.driver.move_to(0, row)
        self.driver.putstr(lines[row])

    # And set it to input afterwards to let voltameter
    # to use it as polarity pin
    self.driver.data[3].init(Pin.IN)

    self.shown = lines

  @micropython.native
  def set_text(self, text_up: str | None = None, text_down: str | None = None):
    self.update = True
    self.text = [text_up or "", text_down or ""]

  @micropython.native
  def clear_text(self):
    self.update = True
    self.text = ["", ""]

  @micropython.native
  def set_overlay(self, text_up: str | None = None, text_down: str | None = None):
    self.update = True
    self.overlay = [text_up, text_down]

  @micropython.native
  def clear_overlay(self):
    self.update = True
    self.overlay = [None, None]
