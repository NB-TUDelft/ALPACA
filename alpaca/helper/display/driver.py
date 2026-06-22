from machine import Pin
from time import sleep_us, sleep_ms

# Driver for the HD44780 LCD Display on the board
# Based on https://github.com/wjdp/micropython-lcd/blob/master/lcd.py
class HD44780:
    def __init__(self, rs, e, data_pins):
        self.rs = Pin(rs, Pin.OUT)
        self.e = Pin(e, Pin.OUT)
        self.data = [Pin(p, Pin.OUT) for p in data_pins]  # DB4..DB7
        self.e.value(0)
        sleep_ms(50)  # wait for LCD power-up

        # Force into 4-bit mode (HD44780 init dance)
        self._write4(0x03)
        sleep_ms(5)
        self._write4(0x03)
        sleep_us(150)
        self._write4(0x03)
        sleep_us(150)
        self._write4(0x02)
        sleep_us(150)

        self._cmd(0x28)  # function set: 4-bit, 2 lines, 5x8 font
        self._cmd(0x0C)  # display on, cursor off, blink off
        self._cmd(0x06)  # entry mode: increment, no shift
        self.clear()

    def _pulse(self):
        self.e.value(1)
        sleep_us(1)
        self.e.value(0)
        sleep_us(100)

    def _write4(self, nibble):
        for i in range(4):
            self.data[i].value((nibble >> i) & 1)
        self._pulse()

    def _send(self, value, rs):
        # self.rs.init(Pin.OUT)
        self.rs.value(rs)
        self._write4(value >> 4)
        self._write4(value & 0x0F)

    def _cmd(self, value):
        self._send(value, 0)
        sleep_us(50)

    def _char(self, value):
        self._send(value, 1)
        sleep_us(50)

    def clear(self):
        self._cmd(0x01)
        sleep_ms(2)

    def move_to(self, col, row):
        self._cmd(0x80 | (col + (0x40 if row else 0x00)))

    def putstr(self, s):
        for ch in s:
            self._char(ord(ch))


# HD44780 LCD wiring (4-bit mode):
#   RS=GP17  E=GP18  RW->GND
#   DB4=GP19  DB5=GP20  DB6=GP21  DB7=GP22
lcd = HD44780(17, 18, [19, 20, 21, 22])