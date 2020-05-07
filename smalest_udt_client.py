import time

import udt
import logging
import socket
import threading

# udt_socket = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
# udt_socket.connect(("127.0.0.1", 50011))

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.connect(("127.0.0.1", 50010))


def recv_data():
    while True:
        # data = udt_socket.recv(1024, 0)
        data = tcp_socket.recv(1024, 0)
        logging.warning("recv data: %s" % data)


def printing():
    while True:
        print("client is still alive...\n")
        time.sleep(1)


r_print = threading.Thread(target=printing)
r_print.start()
logging.warning("printing thread started...")


r_recv = threading.Thread(target=recv_data)
r_recv.start()
logging.warning("receiving thread started...")