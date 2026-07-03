import micropython
from display import display

text_up = ""
text_down = ""

def set_text(_text_up, _text_down):
  global text_up, text_down

  text_up = _text_up
  text_down = _text_down

@micropython.native
def display_custom(last_tick):
  display.set_text(text_up, text_down)
