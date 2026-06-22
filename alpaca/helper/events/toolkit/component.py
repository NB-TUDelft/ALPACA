import micropython
from machine import Pin, ADC
from time import sleep_ms, ticks_ms, ticks_diff, sleep_us

from display import display

# Component tester front end:
#
#   GPIO15 --10k-- PROBE A --10k-- ADC2 (28)
#   GPIO14 --10k-- PROBE B --10k-- ADC1 (27)
#
# Each probe is driven by a GPIO through a 10k series resistor and sensed by an
# ADC (the ADC's own 10k is harmless -- the ADC draws ~no current, so it reads
# the probe-node voltage). The device under test (DUT) bridges PROBE A to PROBE
# B. By driving the probes as a complementary pair (one high, one low) we form a
# series divider  3V3 - 10k - A -[DUT]- B - 10k - GND  and read both nodes.

_PROBE_A_PIN = const(14)
_PROBE_B_PIN = const(15)
_ADC_A_PIN = const(28)
_ADC_B_PIN = const(27)  # senses PROBE B

_ADC_RANGE = const(3.3 / 2**16)

_SAMPLES = const(4)       # readings averaged per node

# Classification thresholds, in ADC counts / ohms.
_OPEN_COUNTS = const(800)  # low-side voltage below this == no current flows
_SHORT_OHMS = const(50)    # below this the DUT is treated as a short

_OMEGA = "\xf4"   # HD44780 ROM code for the ohm symbol
_ARROW = "\x7e"   # HD44780 ROM code for the right arrow


probe_a = Pin(_PROBE_A_PIN)
probe_b = Pin(_PROBE_B_PIN)
adc_a = ADC(_ADC_A_PIN)
adc_b = ADC(_ADC_B_PIN)

N_AVG = const(15)

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
def display_component(last_tick):

  set_direction("forward")

  val_adc_a = read_adc(adc_a)
  val_adc_b = read_adc(adc_b)

  v_drop = val_adc_a - val_adc_b

  R = 20e3 / (3.3 - v_drop) * v_drop

  display.set_text(f"{R:.2f}", "RESISTOR")

  # if isCap:
  #   return display.set_text("CAPACITOR", f"{C:.2f}F")
