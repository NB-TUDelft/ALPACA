from time import ticks_diff, ticks_ms
import micropython
from display.driver import HD44780

_VOLTAGE_REFRESH_RATE = const(4) # Hz
_VOLTAGE_PERIOD_MS = const(1000 // _VOLTAGE_REFRESH_RATE)

class LCDManager():
  def __init__(self) -> None:
    self.driver = HD44780(17, 18, [19, 20, 21, 22])

    self.text = ["", ""]
    self.overlay = [None, None]
    self.update = False

  def draw(self, last_tick):
    if not self.update:
      return True

    if ticks_diff(ticks_ms(), last_tick) < _VOLTAGE_PERIOD_MS:
      return True
    
    text_0 = self.overlay[0] or self.text[0]
    text_1 = self.overlay[1] or self.text[1]

    self.driver.clear()
    
    self.driver.move_to(0, 0)
    self.driver.putstr(text_0)
    self.driver.move_to(0, 1)
    self.driver.putstr(text_1)

    self.update = False

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
