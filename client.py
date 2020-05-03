import json  # json.dumps(some)打包   json.loads(some)解包
from udt_video_client import register_video_client
from message.message_pb2 import message
import logging
import os
import socket
import struct
import sys
import threading
import time
import tkinter
import tkinter.messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText  # 导入多行文本框用到的包

import udt
from netifaces import interfaces, ifaddresses, AF_INET6

import vachat

EXIT = False
IP = ''
PORT = ''
username = ''
listbox1 = ''  # 用于显示在线用户的列表框
ii = 0  # 用于判断是开还是关闭列表框
users = []  # 在线用户列表
chat = '------Group chat-------'  # 聊天对象, 默认为群聊

# 登陆窗口
root1 = tkinter.Tk()
root1.tk.call('tk', 'scaling', 6.0)
root1.title('Log in')
root1['height'] = 110
root1['width'] = 270
root1.resizable(0, 0)  # 限制窗口大小

IP1 = tkinter.StringVar()
IP1.set('127.0.0.1:50007')  # 默认显示的ip和端口
User = tkinter.StringVar()
User.set('')

# 服务器标签
labelIP = tkinter.Label(root1, text='Server address')
labelIP.place(x=20, y=10, width=100, height=20)

entryIP = tkinter.Entry(root1, width=80, textvariable=IP1)
entryIP.place(x=120, y=10, width=130, height=20)

# 用户名标签
labelUser = tkinter.Label(root1, text='Username')
labelUser.place(x=30, y=40, width=80, height=20)

entryUser = tkinter.Entry(root1, width=80, textvariable=User)
entryUser.place(x=120, y=40, width=130, height=20)


# 登录按钮
def login(*args):
    global IP, PORT, username
    IP, PORT = entryIP.get().split(':')  # 获取IP和端口号
    PORT = int(PORT)  # 端口号需要为int类型
    username = entryUser.get()
    if not username:
        tkinter.messagebox.showerror('Name type error', message='Username Empty!')
    else:
        root1.destroy()  # 关闭窗口


root1.bind('<Return>', login)  # 回车绑定登录功能
but = tkinter.Button(root1, text='Log in', command=login)
but.place(x=100, y=70, width=70, height=30)

root1.mainloop()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.connect((IP, PORT))
if username:
    s.send(username.encode())  # 发送用户名
else:
    s.send('no'.encode())  # 没有输入用户名则标记no

# 如果没有用户名则将ip和端口号设置为用户名
addr = s.getsockname()  # 获取客户端ip和端口号
addr = addr[0] + ':' + str(addr[1])
if username == '':
    username = addr

# 聊天窗口
# 创建图形界面
root = tkinter.Tk()
root.tk.call('tk', 'scaling', 6.0)
root.title(username)  # 窗口命名为用户名
root['height'] = 400
root['width'] = 580
root.resizable(0, 0)  # 限制窗口大小

# 创建多行文本框
listbox = ScrolledText(root)
listbox.place(x=5, y=0, width=570, height=320)
# 文本框使用的字体颜色
listbox.tag_config('red', foreground='red')
listbox.tag_config('blue', foreground='blue')
listbox.tag_config('green', foreground='green')
listbox.tag_config('pink', foreground='pink')
listbox.tag_config('yellow', foreground='yellow')
listbox.tag_config('cyan', foreground='cyan')
listbox.insert(tkinter.END, 'Welcome to the chat room!', 'yellow')


def on_closing():
    global EXIT
    if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
        EXIT = True
        root.destroy()
        sys.exit()


root.protocol("WM_DELETE_WINDOW", on_closing)

# 文件功能代码部分
# 将在文件功能窗口用到的组件名都列出来, 方便重新打开时会对面板进行更新
list2 = ''  # 列表框
label = ''  # 显示路径的标签
upload = ''  # 上传按钮
close = ''  # 关闭按钮


def fileClient():
    PORT2 = 50008  # 聊天室的端口为50007
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((IP, PORT2))

    # 修改root窗口大小显示文件管理的组件
    root['height'] = 390
    root['width'] = 760

    # 创建列表框
    list2 = tkinter.Listbox(root)
    list2.place(x=580, y=25, width=300, height=325)

    # 将接收到的目录文件列表打印出来(dir), 显示在列表框中, 在pwd函数中调用
    def recvList(lu):
        s.send(struct.pack('3si', bytes('ls ', encoding='utf8'), len(lu.encode())))
        s.send(lu.encode())
        data = s.recv(4096)
        data = json.loads(data.decode())
        list2.delete(0, tkinter.END)  # 清空列表框
        lu = lu.split(os.path.sep)
        if len(lu) != 1:
            list2.insert(tkinter.END, 'Return to the previous dir')
            list2.itemconfig(0, fg='green')
        for i in range(len(data)):
            list2.insert(tkinter.END, ('' + data[i]))
            if '.' not in data[i]:
                list2.itemconfig(tkinter.END, fg='orange')
            else:
                list2.itemconfig(tkinter.END, fg='white')

    # 创建标签显示服务端工作目录
    def lab():
        global label
        data = s.recv(1024)  # 接收目录
        lu = data.decode()
        try:
            label.destroy()
            label = tkinter.Label(root, text=lu)
            label.place(x=580, y=0, )
        except:
            label = tkinter.Label(root, text=lu)
            label.place(x=580, y=0, )
        recvList(lu)

    # 进入指定目录(cd)
    def cd(dir):
        s.send(struct.pack('3si', bytes('cd ', encoding='utf8'), len(dir)))
        s.send(dir.encode())

    # 刚连接上服务端时进行一次面板刷新
    cd('same')
    lab()

    # 接收下载文件(get)
    def get(name):
        # print(message)
        # 选择对话框, 选择文件的保存路径
        fileName = tkinter.filedialog.asksaveasfilename(title='Save file to', initialfile=name)
        # 如果文件名非空才进行下载
        if fileName:
            s.send(struct.pack('3si', bytes('get', encoding='utf8'), len(name)))
            s.send(name.encode())
            with open(fileName, 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if data == 'EOF'.encode():
                        tkinter.messagebox.showinfo(title='Message',
                                                    message='Download completed!')
                        break
                    f.write(data)

    # 创建用于绑定在列表框上的函数
    def run(*args):
        indexs = list2.curselection()
        index = indexs[0]
        content = list2.get(index)
        # 如果有一个 . 则为文件
        if '.' in content:
            get(content)
            cd('same')
        elif content == 'Return to the previous dir':
            cd('..')
        else:
            content = 'cd ' + content
            cd(content)
        lab()  # 刷新显示页面

    # 在列表框上设置绑定事件
    list2.bind('<ButtonRelease-1>', run)

    # 上传客户端所在文件夹中指定的文件到服务端, 在函数中获取文件名, 不用传参数
    def put():
        # 选择对话框
        fileName = tkinter.filedialog.askopenfilename(title='Select upload file')
        # 如果有选择文件才继续执行
        if fileName:
            name = fileName.split(os.path.sep)[-1]
            # TODO introduce struct.pack to send command and data
            command = 'put'
            file_header = struct.pack('128sl', bytes(name, encoding='utf8'), os.stat(fileName).st_size)
            header = struct.pack('3si', bytes(command, encoding='utf8'), len(file_header))
            s.send(header)
            s.send(file_header)
            logging.warning("message %s sent to server" % file_header)
            fo = open(fileName, 'rb')
            while True:
                filedata = fo.read(1024)
                if not filedata:
                    break
                s.send(filedata)
            fo.close()
            # with open(fileName, 'rb') as f:
            #     logging.warning("file %s opened" % fileName)
            #     while True:
            #         a = f.read(1024)
            #         if not a:
            #             break
            #         s.send(a)
            logging.warning("file sent")
            tkinter.messagebox.showinfo(title='Message',
                                        message='Upload completed!')
        cd('same')
        lab()  # 上传成功后刷新显示页面

    # 创建上传按钮, 并绑定上传文件功能
    upload = tkinter.Button(root, text='Upload file', command=put)
    upload.place(x=600, y=353, height=30, width=80)

    # 关闭文件管理器, 待完善
    def closeFile():
        root['height'] = 390
        root['width'] = 580
        # 关闭连接
        header = struct.pack('3si', bytes('qui', encoding='utf8'), 0)
        s.send(header)
        s.close()

    # 创建关闭按钮
    close = tkinter.Button(root, text='Close', command=closeFile)
    close.place(x=685, y=353, height=30, width=70)


def UDTfileClient():
    PORT2 = 50008  # 聊天室的端口为50007
    s = udt.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    logging.warning("UDT socket created")
    s.connect((IP, PORT2))
    logging.warning("UDT socket connected to %s:%s" % (IP, PORT2))

    # 创建UDT file pannel
    udt_pannel = tkinter.Tk()
    udt_pannel.tk.call('tk', 'scaling', 6.0)
    udt_pannel.title("UDT File (%s)" % username)
    udt_pannel['height'] = 390
    udt_pannel['width'] = 300
    udt_pannel.resizable(0, 0)

    # 关闭文件管理器, 待完善
    def closeFile():
        udt_pannel.destroy()
        # 关闭连接
        header = struct.pack('3si', bytes('qui', encoding='utf8'), 0)
        s.send(header, 0)
        # 创建关闭按钮

    udt_pannel.protocol("WM_DELETE_WINDOW", closeFile)

    # 将接收到的目录文件列表打印出来(dir), 显示在列表框中, 在pwd函数中调用
    def ls():
        s.send(struct.pack('3si', bytes('ls ', encoding='utf8'), 0), 0)
        data_length = struct.unpack("l", s.recv(struct.calcsize('l'), 0))[0]
        data = s.recv(data_length, 0)
        data = json.loads(data.decode())
        list2.delete(0, tkinter.END)  # 清空列表框
        for i in range(len(data)):
            list2.insert(tkinter.END, ('' + data[i]))
            list2.itemconfig(tkinter.END, fg='white')

    refresh = tkinter.Button(udt_pannel, text='Refresh', command=ls)
    refresh.place(x=105, y=353, height=30, width=70)

    # 创建列表框
    list2 = tkinter.Listbox(udt_pannel)
    list2.place(x=0, y=25, width=300, height=325)

    ls()

    # 接收下载文件(get)
    def get(name):
        # 选择对话框, 选择文件的保存路径
        fileName = tkinter.filedialog.asksaveasfilename(title='Save file to', initialfile=name)
        # 如果文件名非空才进行下载
        if fileName:
            s.send(struct.pack('3si', bytes('get', encoding='utf8'), len(name)), 0)
            s.send(name.encode(), 0)
            file_length = struct.unpack('l', s.recv(struct.calcsize('l'), 0))[0]
            recvd_size = 0
            logging.warning("%s bytes to receive, start receiving..." % file_length)
            start_time = time.time()
            file = open(fileName, 'wb')
            while not recvd_size == file_length:
                if file_length - recvd_size > 1024:
                    rdata = s.recv(1024, 0)
                    recvd_size += len(rdata)
                else:
                    rdata = s.recv(file_length - recvd_size, 0)
                    recvd_size = file_length
                file.write(rdata)
            file.close()
            tkinter.messagebox.showinfo(title='Message',
                                        message='UDT Download completed in %.2fms' % (time.time() - start_time))
            logging.warning('file wrote to %s' % fileName)

    # 创建用于绑定在列表框上的函数
    def run(*args):
        indexs = list2.curselection()
        index = indexs[0]
        content = list2.get(index)
        get(content)
        ls()

    # 在列表框上设置绑定事件
    list2.bind('<ButtonRelease-1>', run)

    # 上传客户端所在文件夹中指定的文件到服务端, 在函数中获取文件名, 不用传参数
    def put():
        # 选择对话框
        fileName = tkinter.filedialog.askopenfilename(title='Select upload file')
        # 如果有选择文件才继续执行
        if fileName:
            name = fileName.split(os.path.sep)[-1]
            # TODO introduce struct.pack to send command and data
            command = 'put'
            file_header = struct.pack('128sl', bytes(name, encoding='utf8'), os.stat(fileName).st_size)
            header = struct.pack('3si', bytes(command, encoding='utf8'), len(file_header))
            s.send(header, 0)
            s.send(file_header, 0)
            logging.warning("message %s sent to server" % file_header)
            fo = open(fileName, 'rb')
            start_time = time.time()
            while True:
                filedata = fo.read(1024)
                if not filedata:
                    break
                s.send(filedata, 0)
            fo.close()
            logging.warning("file sent")
            tkinter.messagebox.showinfo(title='Message',
                                        message='UDT Upload completed in %.2fms' % (time.time() - start_time))
        ls()

    def auto_refresh():
        ls()
        udt_pannel.after(500, func=auto_refresh)

    # 创建上传按钮, 并绑定上传文件功能
    upload = tkinter.Button(udt_pannel, text='Upload file', command=put)
    upload.place(x=20, y=353, height=30, width=80)
    udt_pannel.after(500, func=auto_refresh)
    udt_pannel.mainloop()


# 创建文件按钮
udt_file_button = tkinter.Button(root, text='UDT File', command=UDTfileClient)
udt_file_button.place(x=185, y=320, width=60, height=30)

# 创建多行文本框, 显示在线用户
listbox1 = tkinter.Listbox(root)
listbox1.place(x=445, y=0, width=130, height=320)


def users():
    global listbox1, ii
    if ii == 1:
        listbox1.place(x=445, y=0, width=130, height=320)
        ii = 0
    else:
        listbox1.place_forget()  # 隐藏控件
        ii = 1


# 查看在线用户按钮
button1 = tkinter.Button(root, text='Users online', command=users)
button1.place(x=485, y=320, width=90, height=30)

# 创建输入文本框和关联变量
a = tkinter.StringVar()
a.set('')
entry = tkinter.Entry(root, width=120, textvariable=a)
entry.place(x=5, y=350, width=570, height=40)


def send(*args):
    # 没有添加的话发送信息时会提示没有聊天对象
    users.append('------Group chat-------')
    # users.append('Robot')
    print(chat)
    if chat not in users:
        tkinter.messagebox.showerror('Send error', message='There is nobody to talk to!')
        return
    if chat == username:
        tkinter.messagebox.showerror('Send error', message='Cannot talk with yourself in private!')
        return
    # TODO Add Chinese support
    mes = entry.get() + ':;' + username + ':;' + chat  # 添加聊天对象标记
    s.send(mes.encode())
    a.set('')  # 发送后清空文本框


# 创建发送按钮
button = tkinter.Button(root, text='Send', command=send)
button.place(x=515, y=353, width=60, height=30)
root.bind('<Return>', send)  # 绑定回车发送信息

video_socket = register_video_client("127.0.0.1", 50009, username)

# 视频聊天部分
IsOpen = False  # 判断视频/音频的服务器是否已打开
Resolution = 0  # 图像传输的分辨率 0-4依次递减
Version = 4  # 传输协议版本 IPv4/IPv6
ShowMe = True  # 视频聊天时是否打开本地摄像头
AudioOpen = True  # 是否打开音频聊天


# 私聊功能
def private(*args):
    global chat
    # 获取点击的索引然后得到内容(用户名)
    indexs = listbox1.curselection()
    index = indexs[0]
    if index > 0:
        chat = listbox1.get(index)
        # 修改客户端名称
        if chat == '------Group chat-------':
            root.title(username)
            return
        ti = username + '  -->  ' + chat
        root.title(ti)


# 在显示用户列表框上设置绑定事件
listbox1.bind('<ButtonRelease-1>', private)


# 用于时刻接收服务端发送的信息并打印
def recv():
    global users, EXIT
    while True:
        if EXIT:
            s.close()
            break
        data = s.recv(1024)
        data = data.decode()
        # 没有捕获到异常则表示接收到的是在线用户列表
        try:
            data = json.loads(data)
            users = data
            listbox1.delete(0, tkinter.END)  # 清空列表框
            number = ('   Users online: ' + str(len(data)))
            listbox1.insert(tkinter.END, number)
            listbox1.itemconfig(tkinter.END, fg='green', bg="#f0f0ff")
            listbox1.insert(tkinter.END, '------Group chat-------')
            listbox1.itemconfig(tkinter.END, fg='green')
            for i in range(len(data)):
                listbox1.insert(tkinter.END, (data[i]))
                listbox1.itemconfig(tkinter.END, fg='green')
        except:
            data = data.split(':;')
            data1 = data[0].strip()  # 消息
            data2 = data[1]  # 发送信息的用户名
            data3 = data[2]  # 聊天对象
            markk = data1.split(': ')[1]
            # 判断是不是图片
            pic = markk.split('#')
            if pic[0] == '``':
                data4 = '\n' + data2 + ': '  # 例:名字-> \n名字：
                if data3 == '------Group chat-------':
                    if data2 == username:  # 如果是自己则将则字体变为蓝色
                        listbox.insert(tkinter.END, data4, 'blue')
                    else:
                        listbox.insert(tkinter.END, data4, 'green')  # END将信息加在最后一行
                elif data2 == username or data3 == username:  # 显示私聊
                    listbox.insert(tkinter.END, data4, 'red')  # END将信息加在最后一行
            else:
                data1 = '\n' + data1
                if data3 == '------Group chat-------':
                    if data2 == username:  # 如果是自己则将则字体变为蓝色
                        listbox.insert(tkinter.END, data1, 'green')
                    else:
                        listbox.insert(tkinter.END, data1, 'yellow')  # END将信息加在最后一行
                    if len(data) == 4:
                        listbox.insert(tkinter.END, '\n' + data[3], 'pink')
                elif data2 == username or data3 == username:  # 显示私聊
                    listbox.insert(tkinter.END, data1, 'red')  # END将信息加在最后一行
            listbox.see(tkinter.END)  # 显示在最后


# 用于时刻接收视频聊天邀请
def recv_video():
    header_length = int.from_bytes(video_socket.recv(4, 0), 'little')
    header_message_string = video_socket.recv(header_length, 0)
    header = message()
    header.ParseFromString(header_message_string)
    logging.warning("received message %s from server" % header.message)
    if header.message == "invitation":
        invite_window = tkinter.Toplevel()
        invite_window.geometry('300x100')
        invite_window.title("Invitation")
        label1 = tkinter.Label(invite_window, bg='#f0f0f0', width=20, text=header.username)
        label1.pack()
        label2 = tkinter.Label(invite_window, bg='#f0f0f0', width=20, text='invites you to video chat!')
        label2.pack()

        def accept_invite():
            invite_window.destroy()
            logging.warning("accepted video invitation")
            accept_message = message()
            accept_message.username = username
            accept_message.message = "accept"
            accept_proto = accept_message.SerializeToString()
            s.send(len(accept_proto).to_bytes(4, 'little'), 0)
            s.send(accept_proto, 0)

        def refuse_invite():
            invite_window.destroy()
            logging.warning("refused video invitation")
            refuse_message = message()
            refuse_message.username = username
            refuse_message.message = "refuse"
            refuse_proto = refuse_message.SerializeToString()
            s.send(len(refuse_proto).to_bytes(4, 'little'), 0)
            s.send(refuse_proto, 0)

        Refuse = tkinter.Button(invite_window, text="Refuse", command=refuse_invite)
        Refuse.place(x=60, y=60, width=60, height=25)
        Accept = tkinter.Button(invite_window, text="Accept", command=accept_invite)
        Accept.place(x=180, y=60, width=60, height=25)


r_chat = threading.Thread(target=recv)
r_chat.start()  # 开始线程接收信息

# r_video = threading.Thread(target=recv_video)
# r_video.start()

root.mainloop()
s.close()  # 关闭图形界面后关闭TCP连接
