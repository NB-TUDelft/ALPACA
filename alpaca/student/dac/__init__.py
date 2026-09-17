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


  def _build_awg_table(self, generator: Callable[[float], float], N: int) -> memoryview:
    # 16-bit message
    # 2 bytes per message
    awg_table = bytearray(N * 2)

    for i in range(N):
      val = int(generator(i / (N - 1)) / self.v_ref)

      data = driver._prepend_header(val, self.channel, gain=self.gain)

      awg_table[i * 2]     = (data >> 8) & 0xFF
      awg_table[i * 2 + 1] = data & 0xFF

    return memoryview(awg_table)


  def generate(self, generator: Callable[[float], float], frequency_hz: int, N: int = 100):
    awg_table = self._build_awg_table(generator, N)

    sample_period_us = int(1_000_000 / (frequency_hz * N))

    if sample_period_us < 1:
      raise ValueError("Sample period can't be less than 1us (1MHz)")

    # Keep the recipe around so DAC.sync can regenerate the table at a
    # shared sample count when resampling both channels.
    return DACWorker(sample_period_us, awg_table, self.channel, self, generator, frequency_hz, N)


  @staticmethod
  def sync(worker_1: "DACWorker", worker_2: "DACWorker", resample: bool = True) -> "SyncedDACWorker":
    """Drive two DAC channels simultaneously.

    Takes two workers (as produced by ``DAC.generate``) that target
    different channels and returns a single worker that interleaves both
    signals over SPI, latching both outputs with one shared LDAC pulse so
    the two channels update at exactly the same instant.

    :param resample: when True (default), both AWG tables are regenerated
      from their original functions at a shared sample count (the larger of
      the two). When the two signals also share a sample period this lets the
      worker drive both channels from a single index on one deadline, instead
      of tracking each channel's deadline separately.

    Usage::

        worker_a = dac_a.generate(...)
        worker_b = dac_b.generate(...)
        with DAC.sync(worker_a, worker_b):
          ...
    """
    if worker_1.channel == worker_2.channel:
      raise ValueError("DAC inputs should be on different channels")

    if resample and worker_1.N != worker_2.N:
      N = max(worker_1.N, worker_2.N)
      worker_1 = worker_1.dac.generate(worker_1.generator, worker_1.frequency_hz, N)
      worker_2 = worker_2.dac.generate(worker_2.generator, worker_2.frequency_hz, N)

    return SyncedDACWorker(worker_1, worker_2)


class DACWorker:
  def __init__(
      self,
      sample_period_us: int,
      awg_table: memoryview,
      channel: Literal[0, 1],
      dac: "DAC",
      generator: Callable[[float], float],
      frequency_hz: int,
      N: int,
    ) -> None:

    # Meta data for sync (channel check + table regeneration)
    self.channel = channel
    self.dac = dac
    self.generator = generator
    self.frequency_hz = frequency_hz
    self.N = N

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


class SyncedDACWorker:
  """Drives two channels from a single worker thread.

  Both signals share one worker loop so their outputs are latched together
  with one LDAC pulse. Each channel keeps its own sample period, so signals
  of different frequencies stay phase-aligned while still updating in lockstep
  whenever their deadlines coincide.
  """
  def __init__(
      self,
      worker_1: "DACWorker",
      worker_2: "DACWorker",
    ) -> None:

    # Pull the metadata we need to drive both channels from one loop
    self.sample_period_1 = worker_1.sample_period_us
    self.awg_table_1 = worker_1.awg_table

    self.sample_period_2 = worker_2.sample_period_us
    self.awg_table_2 = worker_2.awg_table

    self.stop_flag_lock = _thread.allocate_lock()

  def __enter__(self):
    self.stop_flag_lock.acquire()

    self.done = _thread.allocate_lock()
    self.done.acquire()

    # When both tables share a period and a size (e.g. after resampling)
    # a single index on one deadline drives both channels: no per-channel
    # deadline tracking, and both values are pushed before every latch.
    if (self.sample_period_1 == self.sample_period_2
        and len(self.awg_table_1) == len(self.awg_table_2)):
      _thread.start_new_thread(self.worker_locked, (
        self.sample_period_1,
        self.awg_table_1,
        self.awg_table_2,
        self.stop_flag_lock,
        self.done,
        driver.spi,
        driver.cs,
        driver.ldac
      ))
    else:
      _thread.start_new_thread(self.worker, (
        self.sample_period_1,
        self.awg_table_1,
        self.sample_period_2,
        self.awg_table_2,
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
  def worker_locked(period: int,
                    awg_table_1: memoryview,
                    awg_table_2: memoryview,
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

    count = len(awg_table_1)
    next_t = ticks_us()
    i = 0

    while not stop(False):
      # Wait for the shared sample deadline
      while ticks_diff(ticks_us(), next_t) < 0:
        pass

      # Load both channels into their input registers
      cs_val(0)
      spi_write(awg_table_1[i:i+2])
      cs_val(1)

      cs_val(0)
      spi_write(awg_table_2[i:i+2])
      cs_val(1)

      # Latch both channels to their outputs simultaneously
      ldac_val(0)
      ldac_val(1)

      next_t = ticks_add(next_t, period)

      i += 2
      if i >= count:
        i = 0

    done_lock.release()

  @micropython.native
  @staticmethod
  def worker(period_1: int,
             awg_table_1: memoryview,
             period_2: int,
             awg_table_2: memoryview,
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

    count_1 = len(awg_table_1)
    count_2 = len(awg_table_2)

    now = ticks_us()
    next_1 = now
    next_2 = now
    i = 0
    j = 0

    while not stop(False):
      # Wait until at least one channel is due for its next sample
      while ticks_diff(ticks_us(), next_1) < 0 and ticks_diff(ticks_us(), next_2) < 0:
        pass

      updated = False

      # Load channel 1 into its input register if it's due
      if ticks_diff(ticks_us(), next_1) >= 0:
        cs_val(0)
        spi_write(awg_table_1[i:i+2])
        cs_val(1)

        next_1 = ticks_add(next_1, period_1)
        i += 2
        if i >= count_1:
          i = 0
        updated = True

      # Load channel 2 into its input register if it's due
      if ticks_diff(ticks_us(), next_2) >= 0:
        cs_val(0)
        spi_write(awg_table_2[j:j+2])
        cs_val(1)

        next_2 = ticks_add(next_2, period_2)
        j += 2
        if j >= count_2:
          j = 0
        updated = True

      # Latch both channels to their outputs simultaneously
      if updated:
        ldac_val(0)
        ldac_val(1)

    done_lock.release()