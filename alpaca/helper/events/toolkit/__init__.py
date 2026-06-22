import micropython

from time import ticks_ms, ticks_diff

from bus import link
from machine import Pin

from display import display
from events.toolkit.voltmeter import display_voltage
from events.toolkit.component import display_component

_FUNCTION_BTN_PIN = const(16)
func_btn = Pin(_FUNCTION_BTN_PIN, Pin.IN, Pin.PULL_UP)

_MENU_TIMEOUT_MS = const(1500)

active_display = 0
prev_btn = 1
menu_open = False
last_press = 0

DISPLAYS = [
  ("COMP", display_component),
  ("VOLT", display_voltage),
]

@link.event
@micropython.native
def toolkit(last_tick):
  """Render the active instrument screen and drive the function-button menu.

  Pressing the button brings up the screen selector; each further press while
  it's showing cycles to the next instrument, and the selector dismisses
  itself once the button has been idle briefly."""
  global active_display, prev_btn, menu_open, last_press

  btn = func_btn.value()
  pressed = btn == 0 and prev_btn == 1
  prev_btn = btn

  if pressed:
    if menu_open:
      active_display = (active_display + 1) % len(DISPLAYS)
    menu_open = True
    last_press = ticks_ms()

  # Dismiss the menu after 1.5s without a press
  if menu_open and ticks_diff(ticks_ms(), last_press) >= _MENU_TIMEOUT_MS:
    menu_open = False
    display.clear_overlay()

  title, show_display = DISPLAYS[active_display]
  show_display(last_tick)

  if menu_open:
    display.set_overlay("SELECT", f"\x7e{title}")