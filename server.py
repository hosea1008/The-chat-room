import logging
import socket
import udt
import struct
import threading
import queue
import json  # json.dumps(some)打包   json.loads(some)解包
import time
import os
import os.path
import requests
import sys

# IP = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
IP = ''
PORT = 50007
que = queue.Queue()  # 用于存放客户端发送的信息的队列
users = []  # 用于存放在线用户的信息  [conn, user, addr]
lock = threading.Lock()  # 创建锁, 防止多个线程写入数据的顺序打乱


# 将在线用户存入online列表并返回
def onlines():
    online = []
    for i in range(len(users)):
        online.append(users[i][1])
    return online


class ChatServer(threading.Thread):
    global users, que, lock

    def __init__(self, port):
        threading.Thread.__init__(self)
        # self.setDaemon(True)
        self.ADDR = ('', port)
        # self.PORT = port
        os.chdir(sys.path[0])
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.conn = None
        # self.addr = None

    # 用于接收所有客户端发送信息的函数
    def tcp_connect(self, conn, addr):
        # 连接后将用户信息添加到users列表
        user = conn.recv(struct.unpack("I", conn.recv(struct.calcsize("I")))[0])  # 接收用户名
        user = user.decode()

        for i in range(len(users)):
            if user == users[i][1]:
                print('User already exist')
                user = '' + user + '_2'

        if user == 'no':
            user = addr[0] + ':' + str(addr[1])
        users.append((conn, user, addr))
        print(' New connection:', addr, ':', user, end='')  # 打印用户名
        d = onlines()  # 有新连接则刷新客户端的在线用户显示
        self.recv(d, addr)
        try:
            while True:
                data = conn.recv(struct.unpack("I", conn.recv(struct.calcsize("I")))[0])  # 接收用户名
                data = data.decode()
                if data == "goodbye":
                    self.delUsers(conn, addr)
                    lock.acquire()
                    conn.send(struct.pack("I", len("goodbye".encode())))
                    conn.send("goodbye".encode())
                    lock.release()
                    break
                self.recv(data, addr)  # 保存信息到队列
            conn.close()
        except:
            print(user + ' Connection lose')
            self.delUsers(conn, addr)  # 将断开用户移出users
            conn.close()

    # 判断断开用户在users中是第几位并移出列表, 刷新客户端的在线用户显示
    def delUsers(self, conn, addr):
        a = 0
        for i in users:
            if i[0] == conn:
                users.pop(a)
                print(' Remaining online users: ', end='')  # 打印剩余在线用户(conn)
                d = onlines()
                self.recv(d, addr)
                print(d)
                break
            a += 1

    # 将接收到的信息(ip,端口以及发送的信息)存入que队列
    def recv(self, data, addr):
        lock.acquire()
        try:
            que.put((addr, data))
        finally:
            lock.release()

    # 将队列que中的消息发送给所有连接到的用户
    def sendData(self):
        while True:
            time.sleep(0.1)
            if not que.empty():
                data = ''
                reply_text = ''
                message = que.get()  # 取出队列第一个元素
                if isinstance(message[1], str):  # 如果data是str则返回Ture
                    for i in range(len(users)):
                        # user[i][1]是用户名, users[i][2]是addr, 将message[0]改为用户名
                        for j in range(len(users)):
                            if message[0] == users[j][2]:
                                # TODO Add Chinese support
                                data = ' ' + users[j][1] + ': ' + message[1]
                                break
                        lock.acquire()
                        users[i][0].send(struct.pack("I", len(data.encode())))
                        users[i][0].send(data.encode())
                        lock.release()
                # data = data.split(':;')[0]
                if isinstance(message[1], list):  # 同上
                    # 如果是list则打包后直接发送  
                    data = json.dumps(message[1])
                    for i in range(len(users)):
                        try:
                            lock.acquire()
                            users[i][0].send(struct.pack("I", len(data.encode())))
                            users[i][0].send(data.encode())
                            lock.release()
                        except:
                            pass

    def run(self):

        self.s.bind(self.ADDR)
        self.s.listen(5)
        print('Chat server starts running...')
        q = threading.Thread(target=self.sendData)
        q.start()
        while True:
            conn, addr = self.s.accept()
            t = threading.Thread(target=self.tcp_connect, args=(conn, addr))
            t.start()


################################################################
class UDTFileServer(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        # self.setDaemon(True)
        self.ADDR = ('0.0.0.0', port)
        # self.PORT = port
        self.s = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        # self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.first = r'.%sudt_resources' % os.path.sep
        os.chdir(self.first)  # 把first设为当前工作路径

    def udt_connect(self, conn, addr):
        print(' Connected by: ', addr)

        while True:
            header = conn.recv(struct.calcsize('3si'), 0)
            command, message_length = struct.unpack('3si', header)
            message = conn.recv(message_length, 0)
            command = command.decode()
            # TODO introduce struct.pack to handle data and command
            if command == 'qui':
                print('Disconnected from {0}'.format(addr))
                break
            self.recv_func(command, message, conn)
        conn.close()

    # 传输当前目录列表
    def sendList(self, conn):
        listdir = os.listdir(os.getcwd())
        listdir = json.dumps(listdir)
        conn.send(struct.pack('i', len(listdir.encode())), 0)
        conn.send(listdir.encode(), 0)

    # 发送文件函数
    def sendFile(self, message, conn):
        name = message.strip()  # 获取第二个参数(文件名)
        fileName = r'.%s' % os.path.sep + name
        file_length = os.stat(fileName).st_size
        conn.send(struct.pack('i', file_length), 0)
        fo = open(fileName, 'rb')
        while True:
            filedata = fo.read(1024)
            if not filedata:
                break
            conn.send(filedata, 0)
        fo.close()
        logging.warning("file sent")

    # 保存上传的文件到当前工作目录
    def recvFile(self, message, conn):
        name, file_length = struct.unpack('128si', message)
        name = name.strip(b'\00').decode()
        file_name = r'.%s' % os.path.sep + name.strip()

        logging.warning('filesize is: %s\t\tfilename is: %s' % (file_length, file_name))
        recvd_size = 0  # 定义接收了的文件大小
        file = open(file_name, 'wb')
        logging.warning('stat receiving...')
        while not recvd_size == file_length:
            if file_length - recvd_size > 1024:
                rdata = conn.recv(1024, 0)
                recvd_size += len(rdata)
            else:
                rdata = conn.recv(file_length - recvd_size, 0)
                recvd_size = file_length
            file.write(rdata)
        file.close()
        logging.warning('file wrote to %s' % file_name)

    # 切换工作目录
    def cd(self, message, conn):
        path = os.getcwd().split(os.path.sep)  # 当前工作目录
        for i in range(len(path)):
            if path[i] == 'udt_resources':
                break
        pat = ''
        for j in range(i, len(path)):
            pat = pat + path[j] + ' '
        pat = os.path.sep.join(pat.split())
        # 如果切换目录超出范围则退回切换前目录
        if 'udt_resources' not in path:
            f = r'.%sudt_resources' % os.path.sep
            os.chdir(f)
            pat = 'udt_resources'
        conn.send(pat.encode(), 0)

    # 判断输入的命令并执行对应的函数
    def recv_func(self, command, message, conn):
        if command != 'ls ':
            logging.warning("receive command %s message %s" % (command, message))
        if command == 'get':
            return self.sendFile(message.decode(), conn)
        elif command == 'put':
            return self.recvFile(message, conn)
        elif command == 'ls ':
            return self.sendList(conn)
        # elif command == 'cd ':
        #     return self.cd(message.decode(), conn)

    def run(self):
        print('File server starts running...')
        self.s.bind(self.ADDR)
        self.s.listen(10)
        while True:
            conn, addr = self.s.accept()
            logging.warning("connection accepted")
            t = threading.Thread(target=self.udt_connect, args=(conn, addr))
            t.start()


#############################################################################


if __name__ == '__main__':
    cserver = ChatServer(PORT)
    fserver = UDTFileServer(PORT + 1)
    cserver.start()
    fserver.start()
    while True:
        time.sleep(1)
        if not cserver.isAlive():
            print("Chat connection lost...")
            sys.exit(0)
        if not fserver.isAlive():
            print("File connection lost...")
            sys.exit(0)
