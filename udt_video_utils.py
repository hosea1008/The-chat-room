import pickle
import socket
from PIL import Image, ImageTk
import tkinter

import cv2

from message.message_pb2 import message, metadata

import udt
import logging


def list_split(data, length):
    return [data[m:m + length] for m in range(0, len(data), length)]


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
    header_length = int.from_bytes(conn.recv(4), 'little')
    header_message_string = conn.recv(header_length)
    command = message()
    command.ParseFromString(header_message_string)
    return command


def tcp_send_command(command, conn):
    command_proto = command.SerializeToString()
    conn.send(len(command_proto).to_bytes(4, 'little'))
    conn.send(command_proto)


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


class VideoFeeder:
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
            data_list = list_split(data, 1024)

            data_header = message()
            data_header.username = self.username
            data_header.message = "data"
            data_header.messageLength = len(data)

            data_meta = data_header.meta.add()
            data_meta.packageSize = 1024
            data_meta.packageCount = len(data_list)
            data_meta.tailSize = len(data_list[-1])

            udt_send_command(data_header, self.data_tunnel)

            for data_package in data_list:
                self.data_tunnel.send(data_package, 0)

            img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.video_label.imgtk = img
            self.video_label.config(image=img)
            self.video_label.after(int(1000 / self.fps), self.show_frame)

    def start(self):
        self.is_feeding = True
        self.create_window()
        self.show_frame()


class VideoReceiver:
    def __init__(self,
                 command_tunnel,
                 data_tunnel,
                 username):
        self.command_tunnel = command_tunnel
        self.data_tunnel = data_tunnel
        self.username = username,

    def recv_frame(self):
        is_finished = False
        frame = None
        error = None

        data_header = udt_recv_command(self.data_tunnel)

        if data_header.message == "videofinish":
            logging.warning("video share finished")
            is_finished = True
        elif data_header.message == "data":
            data_length = data_header.messageLength
            data_meta = data_header.meta[0]
            package_size = data_meta.packageSize
            package_count = data_meta.packageCount
            tail_size = data_meta.tailSize

            try:
                data_list = []
                for i in range(package_count - 1):
                    data_list.append(self.data_tunnel.recv(package_size, 0))
                data_list.append(self.data_tunnel.recv(tail_size, 0))

                data = b''.join(data_list)
                if data_length != len(data):
                    logging.warning("invalid frame received, expecte %d bytes, got %s bytes" % (data_length, len(data)))
                    error = "invalid frame"

                frame = pickle.loads(data)
            except Exception as e:
                error = str(e)

            if frame is None:
                error = "empty frame"

        return error, is_finished, frame
