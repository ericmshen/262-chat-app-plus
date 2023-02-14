import sys
import socket
import selectors
import traceback
from typing import Tuple
import types
from collections import defaultdict
from _thread import *
import threading

sel = selectors.DefaultSelector()
# maintain a dictionary of messages
messages = defaultdict(list)
messages["eric"] = ["hello my love"]
threads = []

host = "127.0.0.1"
port = 22067

# keeps track of all registered users
registeredUsers = set()
# mapping from user to connected socket; also serves as a directory of online users
userToSocket = dict()

def accept_wrapper( sock):
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(sock):
    while True:
        # read 50 bytes for the command
        command = sock.recv(1)
        command = int.from_bytes(command, "big")
        print(f"client issues command {command}")
        if command == 0:
            username = sock.recv(50).decode('utf-8')
            if username in registeredUsers:
                msg = f"the username {username} is already registered. please login"
                sock.sendall(bytes(msg, 'utf-8'))
            else:
                registeredUsers.add(username)
                msg = f"the user {username} has succesfully been registered"
                sock.sendall(bytes(msg, 'utf-8'))
        # wait for the user to input a username and map it to the current socket
        elif command == 1:
            # username lengths are limited to 50 bytes
            username = sock.recv(50).decode('utf-8')
            if username in registeredUsers:
                print(f"welcome back {username}")
                if username in userToSocket:
                    msg = f"the user {username} has already logged in another terminal window"
                    sock.sendall(bytes(msg, 'utf-8'))
                else:
                    userToSocket[username] = sock
            # prompt the user to register if they try to login with an unregistered username
            else:
                msg = f"the username {username} is not in the system. please register before logging in"
                sock.sendall(bytes(msg, 'utf-8'))
            # on login we deliver all undelivered messages
            numUndelivered = len(messages[username])
            msg = f"you have {numUndelivered} unread messages"
            sock.sendall(bytes(msg, 'utf-8'))
            if numUndelivered > 0:
                print("".join(messages[username]))
                sock.sendall(bytes("".join(messages[username]), 'utf-8'))
                messages[username] = []
        # this means the command is actually a message that is being sent
        elif command == 2:
            # TODO: change the # bytes here
            message = sock.recv(1024).decode('utf-8').split("|")
            sender, recipient, msg = message[0], message[1], message[2]
            # check if the recipient is logged in, and if so deliver instantaneously
            if recipient in userToSocket:
                print(f"sending to {recipient}")
                userToSocket[recipient].sendall(bytes(f"{sender}: {msg}", 'utf-8'))
            # otherwise, store the message
            else:
                messages[recipient].append(f"{sender}|{msg}")
        elif command == "delete":
            userToDelete = sock.recv(50).decode('utf-8')
            # if the user is connected via the socket they are calling delete from we can delete their account
            if sock == userToSocket[userToDelete]:
                del userToSocket[userToDelete]
            else:
                print("you may not delete another user's account")

        else:
            print("error in the command")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
print("socket binded to port", port)

# put the socket into listening mode
sock.listen(5)
print("socket is listening")

try:
    # a forever loop until client wants to exit
    while True:
        # establish connection with client
        c, addr = sock.accept()      
        print('Connected to :', addr[0], ':', addr[1])

        # Start a new thread and return its identifier
        t = start_new_thread(service_connection, (c,))
        threads.append(t)
except KeyboardInterrupt:
    print("keyboard interrupt closing")
    for c in userToSocket.values:
        c.shutdown(socket.SHUT_RDWR)
        c.close()
    sock.close()