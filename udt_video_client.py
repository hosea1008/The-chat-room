import socket
from message.message_pb2 import message

import udt
import logging


def register_video_client(server_addr, server_port, username):
    s = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    logging.warning("UDT socket created")
    s.connect((server_addr, server_port))
    logging.warning("UDT socket connected to %s:%s" % (server_addr, server_port))

    hello_message = message()
    hello_message.message = "hello"
    hello_message.username = username
    hello_data = hello_message.SerializeToString()
    s.send(len(hello_data).to_bytes(4, 'little'), 0)
    s.send(hello_data, 0)

    return s
