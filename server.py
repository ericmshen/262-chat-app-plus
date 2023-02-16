import socket
import selectors
from collections import defaultdict
from _thread import *
from utils import *
import os

sel = selectors.DefaultSelector()
# maintain a dictionary of messages
messages = defaultdict(list)
threads = []

host, port = "0.0.0.0", 22067
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
print(f"server hostname {socket.gethostname()}")
print("socket bound to port", port)

# put the socket into listening mode
sock.listen(5)
print("socket is listening")
# print hostname for client connection

# keeps track of all registered users
registeredUsers = set()
# mapping from user to connected socket; also serves as a directory of online users
userToSocket = dict()

def service_connection(clientSocket):
    try:
        while True:
            # read 1 byte for the command
            # need to register a logout
            try:
                op = clientSocket.recv(1)
            except:
                print("detected client disconnect, closing connection")
                clientSocket.close()
                return 
            op = int.from_bytes(op, "big")
            if not op:
                print("detected client disconnect, closing connection")
                clientSocket.close()
                return
            status = UNKNOWN_ERROR
            responseHeader = None
            responseBody = None
            print(f">client issued operation code {op}")

            if op == OP_REGISTER:
                print(">>registration requested")
                username = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
                if username in registeredUsers:
                    print(f"{username} is already registered")
                    status = REGISTER_USERNAME_EXISTS
                else:
                    registeredUsers.add(username)
                    print(f"{username} successfully registered")
                    status = REGISTER_OK
            elif op == OP_LOGIN:
                print(">>login requested")
                username = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
                if username in registeredUsers:
                    if username in userToSocket:
                        print(f"{username} is already logged in")
                        status = LOGIN_ALREADY_LOGGED_IN
                    else:
                        # register the socket under the current user's username
                        userToSocket[username] = clientSocket
                        # on login we deliver all undelivered messages
                        numUndelivered = len(messages[username])
                        if numUndelivered > 0:
                            print(f"{username} successfully logged in, {numUndelivered} unread messages")
                            status = LOGIN_OK_UNREAD_MSG
                            responseHeader = numUndelivered
                            responseBody = "\n".join(messages[username])
                            # clear the cache
                            messages[username] = []
                        else:
                            print(f"{username} successfully logged in, no unread messages")
                            status = LOGIN_OK_NO_UNREAD_MSG
                else:
                    print(f"{username} is not registered")
                    status = LOGIN_NOT_REGISTERED
            elif op == OP_SEARCH:
                print(">>search requested")
                query = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
                matched = searchUsernames(list(registeredUsers), query)
                if matched:
                    responseHeader = len(matched)
                    responseBody = "|".join(matched)
                    print(f"search executed, {responseHeader} results")
                    status = SEARCH_OK
                else:
                    print(f"search executed, no results")
                    status = SEARCH_NO_RESULTS
            elif op == OP_SEND:
                print(">>send requested")
                messageRaw = clientSocket.recv(
                    MESSAGE_LENGTH + 
                    2 * USERNAME_LENGTH + 
                    2 * DELIMITER_LENGTH ).decode('ascii').split("|")
                sender, recipient, message = messageRaw[0], messageRaw[1], messageRaw[2]
                # check if the recipient exists
                if recipient not in registeredUsers:
                    print(f"recipient {recipient} is not registered")
                    status = SEND_RECIPIENT_DNE
                # check if the recipient is logged in, and if so deliver instantaneously
                elif recipient in userToSocket:
                    userToSocket[recipient].sendall(
                        RECEIVE_OK.to_bytes(1, "big") +
                        bytes(f"{sender}|{message}", 'ascii')
                    )
                    print(f"sent message from {sender} to {recipient}")
                    status = SEND_OK_DELIVERED
                # otherwise, store the message
                else:
                    print(f"buffered message from {sender} to {recipient}")
                    messages[recipient].append(f"{sender}|{message}")
                    status = SEND_OK_BUFFERED
            elif op == OP_LOGOUT:
                print(">>logout requested")
                userToLogout = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
                del userToSocket[userToLogout]
                status = LOGOUT_OK
            elif op == OP_DELETE:
                print(">>delete requested")
                userToDelete = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
                del userToSocket[userToDelete]
                registeredUsers.remove(userToDelete)
                status = DELETE_OK
            else:
                # we should never get here
                print(">>unknown operation issued")
                status = BAD_OPERATION
            toSend = status.to_bytes(CODE_LENGTH, "big")
            if responseHeader and responseBody:
                toSend += responseHeader.to_bytes(MSG_HEADER_LENGTH, "big")
                toSend += bytes(responseBody, 'ascii')
            clientSocket.sendall(toSend)
            print("server response given")
    except:
        # TODO: unsure what to do here - what sort of errors could the system throw? we should handle each one differently
        pass

# a forever loop until program exit
while True:
    # establish connection with client
    try:
        c, addr = sock.accept()  
    except KeyboardInterrupt:
        print("\nCaught interrupt, shutting down server")
        for c in userToSocket.values():
            c.close()
        sock.close()
        break 
    except:
        print("Failed to accept socket connection, shutting down server")
        break
    print(f"Connected to new client {addr[0]}:{addr[1]}")

    # start a new thread and return its identifier
    t = start_new_thread(service_connection, (c,))
    threads.append(t)
