import socket
import logging
import struct

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
logging.warning("TCP socket created")
s.connect(("127.0.0.1", 50009))
logging.warning("TCP socket connected to %s:%s" % ("127.0.0.1", 50009))

data = s.recv(1024)
logging.warning("received message: %s" % data)