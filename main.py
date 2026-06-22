# pyright: reportMissingModuleSource=false

import belay



# Helper - /dev/cu.usbmodem1101   (standalone, no Belay)
# Student - /dev/cu.usbmodem1401
student = belay.Device("/dev/cu.usbmodem1401")
helper = belay.Device("/dev/cu.usbmodem1101")


student("from machine import Pin")
student('Pin(25, Pin.OUT).value(1)')


# @student.setup
# def setup_link():
#     import ujson
#     from machine import Pin, UART

#     global _link, _next_id
#     _link = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1), timeout=1000)
#     _next_id = 0

#     def _read_reply():
#         # Read one newline-terminated JSON object (honours UART timeout).
#         raw = _link.readline()
#         if not raw:
#             raise OSError("RPC timeout: no reply from helper")
#         return ujson.loads(raw)

#     def call(method, *params):
#         """Send a JSON-RPC request and block for the matching result."""
#         global _next_id
#         _next_id += 1
#         req_id = _next_id
#         _link.write(ujson.dumps(
#             {"jsonrpc": "2.0", "method": method, "params": list(params), "id": req_id}
#         ) + "\n")

#         reply = _read_reply()
#         if reply.get("id") != req_id:
#             raise OSError("RPC id mismatch: sent %s got %s" % (req_id, reply.get("id")))
#         if "error" in reply:
#             err = reply["error"]
#             raise RuntimeError("RPC error %s: %s" % (err.get("code"), err.get("message")))
#         return reply.get("result")

#     def notify(method, *params):
#         """Fire-and-forget: no id, no reply waited for."""
#         _link.write(ujson.dumps(
#             {"jsonrpc": "2.0", "method": method, "params": list(params)}
#         ) + "\n")

#     global _call, _notify
#     _call = call
#     _notify = notify


# @student.task
# def send(method, *params):
#     """Blocking RPC call; returns the helper's result (or raises on error)."""
#     return _call(method, *params)


# @student.task
# def send_async(method, *params):
#     """Fire-and-forget notification; returns immediately, no result."""
#     _notify(method, *params)


# if __name__ == "__main__":
#     setup_link()
#     print("ping ->", send("ping"))
#     send("write", "Hello", "from student")
