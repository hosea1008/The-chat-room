import pickle
import socket
from PIL import Image, ImageTk
import tkinter

import cv2

from message.message_pb2 import message

import udt
import logging


def register_video_client(server_addr, tcp_port, udt_port, username, client_uuid):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_addr, tcp_port))
    logging.warning("TCP socket connected to %s:%s" % (server_addr, tcp_port))

    udt_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    header_length = int.from_bytes(conn.recv(4), 'big')
    header_message_string = conn.recv(header_length)
    command = message()
    command.ParseFromString(header_message_string)
    return command


def udt_send_command(command, conn):
    command_proto = command.SerializeToString()
    conn.send(len(command_proto).to_bytes(4, 'big'))
    conn.send(command_proto)


class VideoFeeder():
    def __init__(self, cap,
                 command_tunnel,
                 data_tunnel,
                 username,
                 frame_size,
                 fps):
        self.is_feeding = True
        self.cap = cap
        self.username = username
        self.command_tunnel = command_tunnel
        self.data_tunnel = data_tunnel
        self.frame_width = frame_size[0]
        self.frame_height = frame_size[1]
        self.fps = fps

        self.video_window = None

    def stop(self):
        self.is_feeding = False
        finish_command = message()
        finish_command.message = "videofinish"
        finish_command.username = self.username

        tcp_send_command(finish_command, self.command_tunnel)
        udt_send_command(finish_command, self.data_tunnel)

        self.cap.release()
        self.video_window.destroy()

        logging.warning("video share finished...")

    def create_window(self):
        self.video_window = tkinter.Toplevel()
        self.video_window.protocol("WM_DELETE_WINDOW", self.stop)
        self.video_window.title("You")
        self.video_window['height'] = self.frame_height + 30
        self.video_window['width'] = self.frame_width
        self.video_window.resizable(0, 0)

        self.video_label = tkinter.Label(self.video_window)
        self.video_label.pack()

        button_finish = tkinter.Button(self.video_window, text="FINISH", command=self.stop)
        button_finish.place(x=0, y=self.frame_height + 15, width=self.frame_width, height=25)
        button_finish.pack()

    def show_frame(self):
        if self.is_feeding:
            _, frame = self.cap.read()
            frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            data = pickle.dumps(frame)
            data_header = message()
            data_header.message = "data"
            data_header.messageLength = len(data)
            udt_send_command(data_header, self.data_tunnel)
            self.data_tunnel.send(data)

            img = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.video_label.imgtk = img
            self.video_label.config(image=img)
            self.video_label.after(int(1000 / self.fps), self.show_frame)

    def start(self):
        self.is_feeding = True
        self.create_window()
        self.show_frame()
