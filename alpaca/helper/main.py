from command import *
from bus import link

@link.register(PING)
def ping_cmd():
  return 1

import events

link.serve()