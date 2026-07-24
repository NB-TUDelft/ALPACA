import micropython
from machine import Pin, ADC
from utime import sleep_ms, ticks_ms, ticks_us, ticks_diff, sleep_us
from math import log

from display import display

_PROBE_A_PIN = const(14)
_PROBE_B_PIN = const(15)

_ADC_A_PIN = const(28)
_ADC_B_PIN = const(27)

_ADC_RANGE = const(3.3 / 2**16)

_OMEGA = "\xf4"
_ARROW = "\x7e"
_ARROW_L = "\x7f"

probe_a = Pin(_PROBE_A_PIN)
probe_b = Pin(_PROBE_B_PIN)

adc_a = ADC(_ADC_A_PIN)
adc_b = ADC(_ADC_B_PIN)

N_AVG = const(60)

def read_adc(adc: ADC):
  raw_a = sum(adc.read_u16() for _ in range(N_AVG)) / N_AVG

  return raw_a * _ADC_RANGE

def set_direction(direction): # typing.Literal["forward", "reverse"] | None = None
  if direction == "forward": # A -> B
    probe_a.init(Pin.OUT)
    probe_b.init(Pin.OUT)
  
    probe_a.value(1)
    probe_b.value(0)
  elif direction == "reverse": # B -> A
    probe_a.init(Pin.OUT)
    probe_b.init(Pin.OUT)

    probe_a.value(0)
    probe_b.value(1)
  else:
    probe_a.init(Pin.IN)
    probe_b.init(Pin.IN)

@micropython.native
def fmt_k(num):
  if num > 1e3:
    return f"{(num / 1000):.2f}k"
  else:
    return f"{round(num)}"

@micropython.native
def fmt_f(c):
  if c >= 1e-6:
    return f"{(c * 1e6):.2f}uF"
  elif c >= 1e-9:
    return f"{(c * 1e9):.2f}nF"
  else:
    return f"{(c * 1e12):.0f}pF"

FLANKING_R = const(330) # Ohms

def is_resistor():
  set_direction("forward")
  val_adc_a = read_adc(adc_a)
  val_adc_b = read_adc(adc_b)

  v_drop = val_adc_a - val_adc_b

  R = (2 * FLANKING_R) / (3.3 - v_drop) * v_drop

  if (R > 80e3):
    return (False, 0)
  else:
    return (True, R)

PROBE_TIME_US = const(50000)   # 50 ms in microseconds

_CAP_THRESH_RAW = const(3277)  # 0.165 V: 10% of the 1.65 V initial divider point
_CAP_DONE_RAW = const(655)     # ~33 mV: DUT considered discharged
_CAP_T_MIN_US = const(50)      # faster crossings are open circuit / stray capacitance
_LN10 = 2.302585

@micropython.native
def is_capacitor():
  probe_a.init(Pin.OUT)
  probe_b.init(Pin.OUT)
  probe_a.value(0)
  probe_b.value(0)

  start = ticks_us()
  while adc_a.read_u16() > _CAP_DONE_RAW:
    if ticks_diff(ticks_us(), start) > PROBE_TIME_US:
      break
    sleep_us(100)

  set_direction("forward")
  start = ticks_us()

  while adc_b.read_u16() > _CAP_THRESH_RAW:
    if ticks_diff(ticks_us(), start) > PROBE_TIME_US:
      set_direction(None)
      return (False, 0) 

  t = ticks_diff(ticks_us(), start)
  set_direction(None)

  if t < _CAP_T_MIN_US:
    return (False, 0)

  return (True, t * 1e-6 / (_LN10 * 2 * FLANKING_R))

_DIODE_COND_V = const(3.0)  # DUT drop below this means current is flowing

def is_diode():
  set_direction("forward")
  sleep_ms(1)
  v_fwd = read_adc(adc_a) - read_adc(adc_b)

  set_direction("reverse")
  sleep_ms(1)
  v_rev = read_adc(adc_b) - read_adc(adc_a)

  set_direction(None)

  conducts_fwd = v_fwd < _DIODE_COND_V
  conducts_rev = v_rev < _DIODE_COND_V

  if conducts_fwd and not conducts_rev:
    return (True, True, v_fwd)
  elif conducts_rev and not conducts_fwd:
    return (True, False, v_rev)
  else:
    return (False, True, 0)


@micropython.native
def display_component(last_tick):
  '''Component tester which can determine whether the DUT (device under test)
  is a resistor, capacitor or a diode and spits out relevant information.
  The circuit is as follows:

  (Probe A)                                (Probe B)
  GPIO14 --330Ohm-(ADC_A)- [DUT] -(ADC_B)-330Ohm-- GPIO15

  The function determines DUT capabilities by setting probes to different
  configurations: forward (3.3V->0V), reverse (0V<-3.3V)
  '''

  isCap, C = is_capacitor()

  if isCap:
    display.set_text(fmt_f(C), "Capacitr")
    return

  isDiode, forward, Vf = is_diode()

  if isDiode:
    arrow = _ARROW if forward else _ARROW_L
    display.set_text(f"1{arrow}2 {Vf:.1f}V", "Diode")
    return

  isRes, R = is_resistor()

  if isRes:
    display.set_text(f"{fmt_k(R)} {_OMEGA}", "Resistor")
    return

  display.set_text("No  Comp", "Detected")
