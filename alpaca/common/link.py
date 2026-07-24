from micropython import const
import micropython
from utime import ticks_ms, ticks_diff, sleep
from command import COMMANDS, pack_args, unpack_args

OK = const(0x00)
ERR = const(0x01)

class Link:
    def __init__(self, uart, timeout_ms=1000):
        self.uart = uart
        self.timeout_ms = timeout_ms
        self.handlers = {}
        self.event_loop = []
        self.event_times = []

    @micropython.native
    def _read_exact(self, n):
        buf = bytearray()
        deadline = ticks_ms()
        while len(buf) < n:
            chunk = self.uart.read(n - len(buf))
            if chunk:
                buf += chunk
                deadline = ticks_ms()  # reset timeout on any progress
            elif ticks_diff(ticks_ms(), deadline) > self.timeout_ms:
                raise OSError("link timeout")
        return bytes(buf)

    @micropython.native
    def _write_frame(self, head, payload):
        self.uart.write(bytes((head, len(payload))) + payload)

    @micropython.native
    def _read_frame(self):
        head = self._read_exact(1)[0]
        n = self._read_exact(1)[0]
        payload = self._read_exact(n) if n else b""
        return head, payload

    @micropython.native
    def call(self, opcode, *args):
        """Send a request and block for the reply. Returns the decoded
        result or raises RuntimeError on an ERR reply."""

        _, args_fmt, ret_fmt = COMMANDS[opcode]

        self.uart.read()  # drain any stale bytes before a fresh exchange
        self._write_frame(opcode, pack_args(args_fmt, args))

        head, payload = self._read_frame()

        if head == ERR:
            raise RuntimeError(payload.decode("utf-8"))

        ret = unpack_args(ret_fmt, payload)

        if not ret:
            return None

        return ret[0] if len(ret) == 1 else ret
    
    def register(self, opcode):
        def _register(func):
            self.handlers[opcode] = func
            return func

        return _register
    
    def event(self, func):
        self.event_loop.append(func)
        self.event_times.append(ticks_ms())

        return func

    @micropython.native
    def serve(self):
        while True:
            # https://docs.micropython.org/en/latest/reference/speed_python.html#the-native-code-emitter
            # Run the scheduler
            sleep(0)

            # Event loop
            for (i, func) in enumerate(self.event_loop):
                if not func(self.event_times[i]):
                    self.event_times[i] = ticks_ms()

            # Non-blocking gate: skip the (blocking) frame read unless a request
            # is already on the wire. Keeps the event loop spinning when idle.
            if not self.uart.any():
                continue

            try:
                opcode, payload = self._read_frame()
            except OSError:
                continue

            # Get command formatting
            entry = COMMANDS.get(opcode)
            handler = self.handlers.get(opcode)

            if entry is None or handler is None:
                self._write_frame(ERR, b"bad opcode")
                continue

            _, args_fmt, ret_fmt = entry
            try:
                result = handler(*unpack_args(args_fmt, payload))
                self._write_frame(OK, pack_args(ret_fmt, _as_tuple(result)))
            except Exception as e:
                self._write_frame(ERR, str(e).encode("utf-8"))


def _as_tuple(result):
    if result is None:
        return ()
    if isinstance(result, tuple):
        return result
    return (result,)
