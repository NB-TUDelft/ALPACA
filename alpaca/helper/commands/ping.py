from command import PING
from bus import link

@link.register(PING)
def ping_cmd():
  return 1