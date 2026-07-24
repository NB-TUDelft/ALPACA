try:
  from typing import Literal
  from collections.abc import Callable
except ImportError:
  pass

from dac.driver import MCP4922
from utime import sleep_us, ticks_diff, ticks_ms, ticks_us, ticks_add
from machine import Pin, SPI
import _thread
import micropython

driver = MCP4922()

class DAC:
  channel: Literal[0, 1]
  gain: Literal[1, 2]

  def __init__(self, channel: Literal["A", "B"], v_ref: Literal[3000, 2048] = 3000, gain: Literal[1, 2] = 1) -> None:
    self.channel = 0 if channel == "A" else 1
    self.v_ref = (v_ref / 1000) / 2**12
    self.gain = gain

  def write(self, val: float):
    driver.write(int(val / self.v_ref), self.channel)


  def generate(self, generator: Callable[[float], float], frequency_hz: int, N: int = 100):
    # 16-bit message
    # 2 bytes per message
    awg_table = bytearray(N * 2)

    for i in range(N):
      val = int(generator(i / (N - 1)) / self.v_ref)

      data = driver._prepend_header(val, self.channel, gain=self.gain)

      awg_table[i * 2]     = (data >> 8) & 0xFF
      awg_table[i * 2 + 1] = data & 0xFF

    sample_period_us = int(1_000_000 / (frequency_hz * N))

    if sample_period_us < 1:
      raise ValueError("Sample period can't be less than 1us (1MHz)")

    return DACWorker(sample_period_us, memoryview(awg_table))


  # @staticmethod
  # def sync(worker_1: DACWorker, worker_2: DACWorker):
  #   if worker_1.dac.channel == worker_2.dac.channel:
  #     return ValueError("DAC inputs should be on different channels")

class DACWorker:
  def __init__(
      self,
      sample_period_us: int,
      awg_table: memoryview,
    ) -> None:

    # # Meta data for sync    
    # self.dac = dac
    # self.generator = generator

    # Actual things to send to worker
    self.sample_period_us = sample_period_us
    self.awg_table = awg_table

    self.stop_flag_lock = _thread.allocate_lock()

  def __enter__(self):
    self.stop_flag_lock.acquire()

    self.done = _thread.allocate_lock()
    self.done.acquire()

    _thread.start_new_thread(self.worker, (
      self.sample_period_us,
      self.awg_table,
      self.stop_flag_lock,
      self.done,
      driver.spi,
      driver.cs,
      driver.ldac
    ))

    return self

  def __exit__(self, exc_type, exc, tb):
    self.stop_flag_lock.release()
    self.done.acquire()

  @micropython.native
  @staticmethod
  def worker(sample_period_us: int,
             awg_table: memoryview,
             stop_flag_lock: _thread.LockType,
             done_lock: _thread.LockType,
             spi: SPI,
             cs: Pin,
             ldac: Pin):

    # Localization (faster accession?)
    cs_val = cs.value
    spi_write = spi.write
    ldac_val = ldac.value
    stop = stop_flag_lock.acquire

    # Opus 4.8 suggested localization of argument
    # should provide optimization, I doubt it
    # on top of that it will also occupy extra
    # space (very tiny but still) in the memory
    period = sample_period_us

    count = len(awg_table)
    next_t = ticks_us()
    i = 0
  
    while not stop(False):
      # Wait for sample deadline
      while ticks_diff(ticks_us(), next_t) < 0:
        pass


      # Write to DAC
      cs_val(0)
      spi_write(awg_table[i:i+2])
      cs_val(1)

      # Shift to Output
      ldac_val(0)
      ldac_val(1)

      next_t = ticks_add(next_t, period)

      i += 2
      if i >= count:
        i = 0

    done_lock.release()