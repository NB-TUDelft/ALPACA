# Student-side client for the Helper Pico link.
# Student code (and the host via Belay) calls these instead of touching the
# wire. Each wrapper is one line over link.call; add one per new opcode.
#
# UART link to the Helper Pico (UART0, crossover + shared GND):
#   Student GP00 (TX) -> Helper GP13 (RX)
#   Student GP01 (RX) <- Helper GP12 (TX)
#   GND <-> GND

from machine import Pin, UART

from command import (
    PING,
    LCD_PUTSTR,
    AWG_R2R_LOAD,
    AWG_R2R_START,
    AWG_R2R_STOP,
    AWG_R2R_OFFSET,
)
from link import Link

link = Link(UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), timeout=1000))

# LOAD frames carry a 2-byte offset + 1-byte blob length, and the frame
# payload caps at 255 bytes, so at most 252 sample bytes fit per chunk.
_AWG_CHUNK = 240

def ping():
    return link.call(PING)

def set_screen_text(text_up = "", text_down = ""):
    return link.call(LCD_PUTSTR, text_up, text_down)

def awg_r2r(samples, sample_rate_hz):
    """Play a waveform on the Helper's R-2R ladder DAC (GPIO0-9).

    samples: iterable of 10-bit codes (0-1023, values are masked), looped
    forever. sample_rate_hz: requested playback rate; returns the actual
    rate achieved, which is lower if the requested rate is too fast.
    """

    link.call(AWG_R2R_STOP)

    n = len(samples)
    buf = bytearray(2 * n)
    for i in range(n):
        v = int(samples[i]) & 0x3FF
        buf[2 * i] = v & 0xFF
        buf[2 * i + 1] = v >> 8

    for off in range(0, len(buf), _AWG_CHUNK):
        link.call(AWG_R2R_LOAD, off, bytes(buf[off:off + _AWG_CHUNK]))

    return link.call(AWG_R2R_START, n, sample_rate_hz)

def awg_r2r_stop():
    """Stop the AWG and drive the ladder to 0."""
    return link.call(AWG_R2R_STOP)

def awg_r2r_offset(magnitude, negative = False):
    """Set the analog offset stage: magnitude 0.0-1.0 (PWM duty on
    OFFSET_PWM), negative selects the sign via OFFSET_POL."""
    return link.call(AWG_R2R_OFFSET, int(magnitude * 65535) & 0xFFFF, negative)
