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
    AWG_R2R_GEN,
    WAVE_SINE,
    WAVE_BLOCK,
    WAVE_TRIANGLE,
    WAVE_SAWTOOTH,
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


class _Waveform:
    """A shortcut waveform the Helper synthesizes itself: playing it sends one
    small payload instead of loading samples over the wire. Use it as a context
    manager so the AWG stops on exit, or drive it with .start()/.stop()."""

    def __init__(self, waveform, frequency_hz, amplitude_vpp, duty_cycle):
        self._waveform = waveform
        self._frequency_hz = frequency_hz
        self._amplitude_vpp = amplitude_vpp
        self._duty_cycle = duty_cycle
        self.frequency_hz = None  # actual rate, filled in by start()

    def start(self):
        self.frequency_hz = link.call(
            AWG_R2R_GEN,
            self._waveform,
            int(self._frequency_hz),
            float(self._amplitude_vpp),
            float(self._duty_cycle),
        )
        return self.frequency_hz

    def stop(self):
        return link.call(AWG_R2R_STOP)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False


class FunctionGenerator:
    """Shortcut waveforms on the Helper's R-2R ladder DAC (GPIO0-9). Amplitudes
    are volts peak-to-peak around mid-rail, clipped to the ladder's 0-3.3V."""

    def sine(self, frequency_hz, amplitude_vpp):
        return _Waveform(WAVE_SINE, frequency_hz, amplitude_vpp, 0.5)

    def block(self, frequency_hz, amplitude_vpp, duty_cycle = 0.5):
        return _Waveform(WAVE_BLOCK, frequency_hz, amplitude_vpp, duty_cycle)

    def triangle(self, frequency_hz, amplitude_vpp):
        return _Waveform(WAVE_TRIANGLE, frequency_hz, amplitude_vpp, 0.5)

    def sawtooth(self, frequency_hz, amplitude_vpp):
        return _Waveform(WAVE_SAWTOOTH, frequency_hz, amplitude_vpp, 0.5)


function_generator = FunctionGenerator()
