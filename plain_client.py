import win32_udt as udt
import socket
import time

udt_socket = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0, "video")
udt_socket.connect(("60.10.4.21", 50002))
for i in range(10):
    # udt_socket.send(b'hello udt', 0)
    print(udt_socket.recv(9, 0))
    time.sleep(0.5)
