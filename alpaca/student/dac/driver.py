try:
  from typing import Literal
except ImportError:
  pass

import micropython
from machine import SPI, Pin
import _thread

_SPIO_SCK_PIN = const(2) # Clock
_SPIO_TX_PIN = const(3) # MOSI
_SPIO_RX_PIN = const(4) # LDAAC
_SPIO_CS_PIN = const(5) # Chip select

DAC_12_BIT_LIMIT = const(2**12 - 1)

class MCP4922:
  """
    MCP4922 is a Digital to Analog Converter

    It operates over SP and has two channels.

    The 16-bit data is sent over TX (MOSI) Pin and 4-bit is reserved
    for config (see MCP4922.write). The data for indiviual channels
    is kept in the input register.

    Setting LDAC to low moves inputs from input register to output
    register, which allows both channels to be operated simeltanously.
  """
  def __init__(self) -> None:
    self.spi = SPI(
      0,
      baudrate=10000000,
      polarity=0,
      phase=0,
      sck=Pin(_SPIO_SCK_PIN),
      mosi=Pin(_SPIO_TX_PIN),
    )

    self.cs = Pin(_SPIO_CS_PIN, Pin.OUT, value=1)
    self.cs.value(1)

    self.ldac = Pin(_SPIO_RX_PIN, Pin.OUT, value=1)
    self.ldac.value(1)

    self._lock = _thread.allocate_lock()

    # Pre-allocate buffer for optimization
    self._buf = bytearray(2)


  @micropython.native
  def _prepend_header(self, value: int, channel: Literal[0, 1] = 0, buffered = False, gain: Literal[1, 2] = 1) -> int:
    """
    Adds header values based on the settings
    
    The payload is 16-bits:
    Bits 0-11: Value
    Bit 12: Shutdown control: 1 - Active, 0 - Shutdown
    Bit 13: Gain select: 2x - 0, 1x - 1
    Bit 14: Buffered
    Bit 15: A/B Channel select

    """
    data = max(0, min(value, DAC_12_BIT_LIMIT))
    
    data |= (1 << 12) # Shutdown control
    
    if gain == 1:
      data |= (1 << 13)
        
    if buffered:
      data |= (1 << 14)
    
    if channel:
      data |= (1 << 15)

    return data


  @micropython.native
  def write(self, value: int, channel: Literal[0, 1] = 0, buffered = False, gain: Literal[1, 2] = 1) -> bool:
    """Write a 12-bit value to DAC
    :param channel: 0 for DAC A, 1 for DAC B.
    :param value: Integer from 0 to 4095.
    :param buffered: True to use VREF buffer, False for unbuffered.
    :param gain: 1x or 2x output gain

    :returns: whether the data was actually sent to DAC
    """

    if not self._lock.acquire(False):
      return False


    data = self._prepend_header(
      value,
      channel,
      buffered,
      gain
    )

    self._buf[0] = (data >> 8) & 0xFF
    self._buf[1] = data & 0xFF

    self.cs.value(0)
    self.spi.write(self._buf)
    self.cs.value(1)

    self.push()

    self._lock.release()

    return True

  @micropython.native
  def push(self):
    """Move input register to output"""
    self.ldac.value(0)
    self.ldac.value(1)
