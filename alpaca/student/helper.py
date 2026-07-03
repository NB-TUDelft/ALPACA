# Student-side client for the Helper Pico link.
# Student code (and the host via Belay) calls these instead of touching the
# wire. Each wrapper is one line over link.call; add one per new opcode.
#
# UART link to the Helper Pico (UART0, crossover + shared GND):
#   Student GP00 (TX) -> Helper GP13 (RX)
#   Student GP01 (RX) <- Helper GP12 (TX)
#   GND <-> GND

from machine import Pin, UART

from command import PING, LCD_PUTSTR
from link import Link

link = Link(UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), timeout=1000))

def ping():
    return link.call(PING)

def set_screen_text(text_up = "", text_down = ""):
    return link.call(LCD_PUTSTR, text_up, text_down)
