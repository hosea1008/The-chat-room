import time
import udt
import logging
import socket
import threading
import select
import multiprocessing

udt_socket = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
# udt_socket.setblocking(False)
udt_socket.connect(("127.0.0.1", 50011))


# tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# tcp_socket.connect(("127.0.0.1", 50010))

epoll = select.epoll()
epoll.register(udt_socket.fileno(), udt.UDT_EPOLL_IN)

def recv_data():
    logging.warning("receive thread started")
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == udt_socket.fileno():
                logging.warning("fileno: %s, udt_socket.fileno: %s" % (fileno, udt_socket.fileno()))
            elif event & select.EPOLLIN:
                data = udt_socket.recv(1024, 0)
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

r_recv.join()