import socket
import udt
import time

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#
udt_s = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
#
# s.bind(("127.0.0.1", 50010))
# s.listen(5)
# conn, addr = s.accept()

udt_s.bind(("0.0.0.0", 50011))
udt_s.listen(5)
conn, addr = udt_s.accept()

# conn.send(b"wake up neo...", 0)

# while True:
#     time.sleep(1)