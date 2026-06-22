from machine import Pin, UART
from link import Link

# The single Link instance shared by every command and event module.
# Import `link` from here (never construct another one) so all the
# @link.register / @link.event decorators attach to the same loop.
link = Link(UART(0, baudrate=115200, tx=Pin(12), rx=Pin(13), timeout=50))
