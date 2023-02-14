import sys
import socket
import selectors
import traceback
from typing import Tuple
import types
from collections import defaultdict

sel = selectors.DefaultSelector()
# maintain a dictionary of messages
messages = defaultdict(list)
messages["eric"] = ["hello my love"]

class Server:
    def __init__(self, host : str, port : int):
        # create a socket that listens for incoming connections from clients
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allows for reuse of port
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen()
        print(f"Listening on {(host, port)}")
        listener.setblocking(False)
        sel.register(listener, selectors.EVENT_READ, data=None)
        self.registeredUsers = set()
        # mapping from user to connected socket; also serves as a directory of online users
        self.userToSocket = dict()
        pass
    
    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        sel.register(conn, events, data=data)

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            # read 50 bytes for the command
            print("PRINTING DATA")
            print(data)
            command = data.outb.decode('utf-8')
            print(command)
            if command:
                print(command)
                if command == "register":
                    username = sock.recv(50)
                    if username in self.registeredUsers:
                        print(f"the username {username} is already registered. please login\n")
                    else:
                        self.registeredUsers.add(username)
                # wait for the user to input a username and map it to the current socket
                elif command == "login":
                    # username lengths are limited to 50 bytes
                    username = sock.recv(50)
                    if username in self.registeredUsers:
                        print(f"welcome back {username}")
                        if self.userToSocket["username"]:
                            print(f"the user {username} has already logged in another terminal window\n")
                            return
                        else:
                            self.userToSocket["username"] = sock
                    # prompt the user to register if they try to login with an unregistered username
                    else:
                        print(f"the username {username} is not in the system. please register before logging in")
                        return
                    # on login we deliver all undelivered messages
                    numUndelivered = len(messages[username])
                    # we use 8 bytes to represent the number of undelivered messages (highly unlikely that there would be more than this)
                    sock.send(numUndelivered.to_bytes(4))
                    sock.send(bytes(messages[username].join("\n"), 'utf-8'))
                # this means the command is actually a message that is being sent
                elif command == "send":
                    # TODO: change the # bytes here
                    message = sock.recv(1024).decode('utf-8').split("|")
                    sender, recipient, msg = message[0], message[1], message[2]
                    # check if the recipient is logged in, and if so deliver instantaneously
                    if recipient in self.userToSocket:
                        sock.send(bytes(messages[username].join("\n"), 'utf-8'))
                    # otherwise, store the message
                    messages[recipient].append(f"{sender}|{msg}")
                elif command == "delete":
                    userToDelete = sock.recv(50)
                    # if the user is connected via the socket they are calling delete from we can delete their account
                    if sock == self.userToSocket[userToDelete]:
                        del self.userToSocket[userToDelete]

                else:
                    print("error in the command\n")
            else:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()
        if mask & selectors.EVENT_WRITE:
            if data.outb:
                print(f"Echoing {data.outb!r} to {data.addr}")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

    def run(self):
        try:
            while True:
                events = sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            sel.close()