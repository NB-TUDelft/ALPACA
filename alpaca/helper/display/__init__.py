from bus import link
from .manager import LCDManager


display = LCDManager()

# Register the bound method (not the raw function) so `self` is supplied.
# Decorating `draw` inside the class body stashes an unbound function, and
# the event loop calls it with only `last_tick` -> missing-arg TypeError.
link.event(display.draw)
