import socket
import time
from message_pb2 import message

import udt
import logging
import struct

s = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
logging.warning("UDT socket created")
s.connect(("127.0.0.1", 50009))
logging.warning("UDT socket connected to %s:%s" % ("127.0.0.1", 50009))

# while True:
#     time.sleep(1)
# data = s.recv(1024, 0)
# logging.warning("received message: %s" % data)
# s.send("hello from udt client".encode(), 0)
message = message()
message.messageLength = 12345.6
message.message = "hello from udt client protobuf"
data = message.SerializeToString()
s.send(len(data).to_bytes(4, 'little'), 0)
s.send(data, 0)
# s.send(struct.pack("Id6s", 100, 23.4, b"Golang"), 0)