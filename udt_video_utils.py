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
    udt_send_command(hello_message, s)
    return s


def udt_recv_command(conn):
    header_length = int.from_bytes(conn.recv(4, 0), 'little')
    header_message_string = conn.recv(header_length, 0)
    command = message()
    command.ParseFromString(header_message_string)
    return command


def udt_send_command(command, conn):
    command_proto = command.SerializeToString()
    conn.send(len(command_proto).to_bytes(4, 'little'), 0)
    conn.send(command_proto, 0)
