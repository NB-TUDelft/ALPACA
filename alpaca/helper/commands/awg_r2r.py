import rp2
import uctypes
from array import array
from micropython import const
from machine import Pin, PWM, freq as sysfreq

from bus import link
from command import AWG_R2R_LOAD, AWG_R2R_START, AWG_R2R_STOP, AWG_R2R_OFFSET

MAX_SAMPLES = const(4096) # 2**12

_LADDER_BITS = const(10)
_OFFSET_POL_PIN = const(10) # Polarity
_OFFSET_PWM_PIN = const(11) # DC Offset
_OFFSET_PWM_FREQ = const(50000)  # far above the 10k/100nF RC filter corner

'''
Instead of CPU generating the form it is split amongst two devices:
- PIO: programmable chip on the Pico that can control the pins
- DMA: moves data from main main memory to the PIO with no CPU
'''


_SM_ID = const(0) # State Machine ID PIO0, PIO1...

# FIFO: first in first out buffer
# Main process writes to TX FIFO and SPIO pulls
_TXF_ADDR = 0x50200000 + 0x100000 * (_SM_ID // 4) + 0x10 + 4 * (_SM_ID % 4)
_TX_DREQ = 8 * (_SM_ID // 4) + (_SM_ID % 4)

_DMA_BASE = const(0x50000000)
_READ_ADDR_TRIG = const(0x3C)  # alias-3 register, offset within a channel
_TREQ_PERMANENT = const(0x3F)

# The SM clock divider bottoms out at sysclk/65536 (~2.3 kHz on an RP2350),
# so rates below _FAST_MIN_RATE use the 256-cycle-per-sample program.
_SLOW_CYCLES = const(256)
_FAST_MIN_RATE = const(2500)
_MIN_RATE = const(10)

# Sample buffer: 16-bit little-endian samples, 10 bits used (0-1023).
buf = bytearray(2 * MAX_SAMPLES)
_addr = array("I", [0])  # buffer address, read by the reload channel

_sm = None
_data_dma = None
_ctrl_dma = None
_offset_pwm = None


# One sample per SM cycle. Autopull refills the OSR every 10 bits shifted;
# the TX FIFOs are joined (8 deep) so playback rides through the loop-seam
# gap while the reload channel retriggers the data channel.
@rp2.asm_pio(
    out_init=(rp2.PIO.OUT_LOW,) * _LADDER_BITS,
    out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopull=True,
    pull_thresh=_LADDER_BITS,
    fifo_join=rp2.PIO.JOIN_TX,
)
def start_awg():
    out(pins, 10)


# 256 SM cycles per sample, for rates below the clock divider floor.
@rp2.asm_pio(
    out_init=(rp2.PIO.OUT_LOW,) * _LADDER_BITS,
    out_shiftdir=rp2.PIO.SHIFT_RIGHT,
    autopull=True,
    pull_thresh=_LADDER_BITS,
    fifo_join=rp2.PIO.JOIN_TX,
)
def start_awg_slow():
    out(pins, 10) [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]
    nop() [31]


def stop_awg():
    global _sm, _data_dma, _ctrl_dma

    # Stop the SM first so the data channel pauses on DREQ and can't
    # complete and chain-retrigger the reload channel mid-teardown.
    if _sm:
        _sm.active(0)
    if _ctrl_dma:
        _ctrl_dma.active(0)
        _ctrl_dma.close()
        _ctrl_dma = None
    if _data_dma:
        _data_dma.active(0)
        _data_dma.close()
        _data_dma = None
    _sm = None


@link.register(AWG_R2R_LOAD)
def awg_r2r_load(offset, data):
    if _sm:
        raise RuntimeError("awg busy, stop first")
    if offset + len(data) > len(buf):
        raise ValueError("awg buffer overflow")
    buf[offset:offset + len(data)] = data


@link.register(AWG_R2R_START)
def awg_r2r_start(nsamples, sample_rate_hz):
    global _sm, _data_dma, _ctrl_dma

    if not 1 <= nsamples <= MAX_SAMPLES:
        raise ValueError("bad sample count")
    if sample_rate_hz < _MIN_RATE:
        raise ValueError("rate too low")

    stop_awg()

    sysclk = sysfreq()
    if sample_rate_hz >= _FAST_MIN_RATE:
        prog, cycles = start_awg, 1
    else:
        prog, cycles = start_awg_slow, _SLOW_CYCLES

    smfreq = sample_rate_hz * cycles
    if smfreq > sysclk:
        smfreq = sysclk

    _sm = rp2.StateMachine(_SM_ID, prog, freq=smfreq, out_base=Pin(0))

    ctrl = rp2.DMA()
    data = rp2.DMA()

    # Reload channel: when the data channel completes it chains here; this
    # rewrites the data channel's read address (via the trigger alias) so
    # the waveform loops with zero CPU.
    _addr[0] = uctypes.addressof(buf)
    ctrl.config(
        read=_addr,
        write=_DMA_BASE + data.channel * 0x40 + _READ_ADDR_TRIG,
        count=1,
        ctrl=ctrl.pack_ctrl(
            size=2,
            inc_read=False,
            inc_write=False,
            treq_sel=_TREQ_PERMANENT,
            chain_to=ctrl.channel,  # no chain
        ),
    )

    # Data channel: stream 16-bit samples into the TX FIFO, paced by the
    # SM's DREQ. Narrow bus writes are replicated across the word, and the
    # program consumes only the low 10 bits of each FIFO entry.
    data.config(
        read=buf,
        write=_TXF_ADDR,
        count=nsamples,
        ctrl=data.pack_ctrl(
            size=1,
            inc_read=True,
            inc_write=False,
            treq_sel=_TX_DREQ,
            chain_to=ctrl.channel,
        ),
        trigger=True,
    )

    _ctrl_dma = ctrl
    _data_dma = data
    _sm.active(1)

    # Exact achieved rate from the 16.8 fractional clock divider.
    div256 = (sysclk * 256 + smfreq // 2) // smfreq
    return int(sysclk * 256 // (div256 * cycles))


@link.register(AWG_R2R_STOP)
def awg_r2r_stop():
    stop_awg()
    # Hand the pins back to SIO, driven low.
    for i in range(_LADDER_BITS):
        Pin(i, Pin.OUT).value(0)


@link.register(AWG_R2R_OFFSET)
def awg_r2r_offset(duty_u16, negative):
    global _offset_pwm
    Pin(_OFFSET_POL_PIN, Pin.OUT).value(1 if negative else 0)
    if _offset_pwm is None:
        _offset_pwm = PWM(Pin(_OFFSET_PWM_PIN))
        _offset_pwm.freq(_OFFSET_PWM_FREQ)
    _offset_pwm.duty_u16(duty_u16)
