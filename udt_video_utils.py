import socket
from message.message_pb2 import message

import udt
import logging


def register_video_client(server_addr, tcp_port, udt_port, username, client_uuid):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_addr, tcp_port))
    logging.warning("TCP socket connected to %s:%s" % (server_addr, tcp_port))

    udt_socket = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    udt_socket.connect((server_addr, udt_port))
    logging.warning("UDT socket connected to %s:%s" % (server_addr, udt_port))

    hello_message = message()
    hello_message.message = "hello"
    hello_message.username = username
    hello_message.uuid = client_uuid

    tcp_send_command(hello_message, tcp_socket)
    udt_send_command(hello_message, udt_socket)
    return tcp_socket, udt_socket


def tcp_recv_command(conn):
    header_length = int.from_bytes(conn.recv(4), 'big')
    header_message_string = conn.recv(header_length)
    command = message()
    command.ParseFromString(header_message_string)
    return command


def tcp_send_command(command, conn):
    command_proto = command.SerializeToString()
    conn.send(len(command_proto).to_bytes(4, 'big'))
    conn.send(command_proto)


def udt_recv_command(conn):
    header_length = int.from_bytes(conn.recv(4, 0), 'big')
    header_message_string = conn.recv(header_length)
    command = message()
    command.ParseFromString(header_message_string)
    return command


def udt_send_command(command, conn):
    command_proto = command.SerializeToString()
    conn.send(len(command_proto).to_bytes(4, 'big'), 0)
    conn.send(command_proto, 0)
