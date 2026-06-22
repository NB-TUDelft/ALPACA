import ustruct as struct

# Opcodes
PING = const(0x01)
LCD_PUTSTR = const(0x02)

# == Command Table
# https://docs.python.org/3/library/struct.html#format-characters
# Some quick reference
# B  unsigned char (0-255)

# Command, input format, output format
COMMANDS = {
    PING: ("ping", "", "B"),
    LCD_PUTSTR: ("lcd_putstr", "ss", ""),
}

def _pack_one(fmt, val):
    if fmt == "B":
        return struct.pack("B", val & 0xFF)
    if fmt == "i":
        return struct.pack(">i", val)
    if fmt == "f":
        return struct.pack(">f", val)
    if fmt == "?":
        return b"\x01" if val else b"\x00" # Faster then 
    if fmt == "s":
        b = val.encode("utf-8")
        return struct.pack("B", len(b)) + b
    raise ValueError("bad fmt: " + fmt)


def _unpack_one(fmt, buf, off):
    if fmt == "B":
        return buf[off], off + 1
    if fmt == "i":
        return struct.unpack(">i", buf[off:off + 4])[0], off + 4
    if fmt == "f":
        return struct.unpack(">f", buf[off:off + 4])[0], off + 4
    if fmt == "?":
        return bool(buf[off]), off + 1
    if fmt == "s":
        n = buf[off]
        return buf[off + 1:off + 1 + n].decode("utf-8"), off + 1 + n

    raise ValueError("bad fmt: " + fmt)


def pack_args(fmt, values):
    """Encode a tuple/list of values per a format string into bytes."""

    out = b""
    for i in range(len(fmt)):
        out += _pack_one(fmt[i], values[i])
    return out


def unpack_args(fmt, buf):
    """Decode bytes per a format string into a list of values."""

    out = []
    off = 0
    for i in range(len(fmt)):
        val, off = _unpack_one(fmt[i], buf, off)
        out.append(val)
    return out
