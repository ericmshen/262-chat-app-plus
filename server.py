import socket
import selectors
from collections import defaultdict
from _thread import *
from utils import *

sel = selectors.DefaultSelector()
# maintain a dictionary of messages
messages = defaultdict(list)
threads = []

host, port = "0.0.0.0", 22068
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
print("socket bound to port", port)

# put the socket into listening mode
sock.listen(5)
print("socket is listening")
# print hostname for client connection
print(f"server hostname {socket.gethostname()}")

# keeps track of all registered users
registeredUsers = set()
# mapping from user to connected socket; also serves as a directory of online users
userToSocket = dict()

def service_connection(sock):
    try:
        while True:
            # read 1 byte for the command
            command = sock.recv(1)
            command = int.from_bytes(command, "big")
            print(f"client issues command {command}")

            opcode = UNKNOWN_ERROR
            responseHeader = None
            responseBody = None

            if command == REGISTER:
                username = sock.recv(USERNAME_LENGTH).decode('ascii')
                if username in registeredUsers:
                    opcode = USERNAME_EXISTS
                else:
                    registeredUsers.add(username)
                    opcode = REGISTRATION_OK
            elif command == LOGIN:
                username = sock.recv(USERNAME_LENGTH).decode('ascii')
                if username in registeredUsers:
                    if username in userToSocket:
                        opcode = ALREADY_LOGGED_IN
                    else:
                        # register the socket under the current user's username
                        userToSocket[username] = sock
                        # on login we deliver all undelivered messages
                        numUndelivered = len(messages[username])
                        if numUndelivered > 0:
                            opcode = LOGIN_OK_UNREAD_MSG
                            responseHeader = numUndelivered
                            responseBody = "\n".join(messages[username])
                            # clear the cache
                            messages[username] = []
                        else:
                            opcode = LOGIN_OK_NO_UNREAD_MSG
                else:
                    opcode = NOT_REGISTERED
            elif command == SEARCH:
                query = sock.recv(USERNAME_LENGTH).decode('ascii')
                matched = searchUsernames(list(registeredUsers), query)
                if matched:
                    responseHeader = len(matched)
                    responseBody = "|".join(matched)
                    opcode = SEARCH_OK
                else:
                    opcode = NO_RESULTS
            elif command == SEND:
                messageRaw = sock.recv(
                    MESSAGE_LENGTH + 
                    2 * USERNAME_LENGTH + 
                    2 * DELIMITER_LENGTH ).decode('ascii').split("|")

                sender, recipient, message = messageRaw[0], messageRaw[1], messageRaw[2]
                # check if the recipient exists
                if recipient not in registeredUsers:
                    opcode = RECIPIENT_DNE
                # check if the recipient is logged in, and if so deliver instantaneously
                elif recipient in userToSocket:
                    userToSocket[recipient].sendall(
                        RECEIVED_INSTANT_OK.to_bytes(1, "big") +
                        bytes(f"{sender}|{message}", 'ascii')
                    )
                    opcode = SENT_INSTANT_OK
                # otherwise, store the message
                else:
                    messages[recipient].append(f"{sender}|{message}")
                    opcode = SENT_CACHED_OK
            elif command == LOGOUT:
                userToLogout = sock.recv(USERNAME_LENGTH).decode('ascii')
                del userToSocket[userToLogout]
                opcode = LOGOUT_OK
            elif command == DELETE:
                userToDelete = sock.recv(USERNAME_LENGTH).decode('ascii')
                del userToSocket[userToDelete]
                registeredUsers.remove(userToDelete)
                opcode = DELETE_OK
            else:
                # we should never get here
                print("error in the command")

            toSend = opcode.to_bytes(OPCODE_LENGTH, "big")
            if responseHeader and responseBody:
                toSend += responseHeader.to_bytes(MSG_HEADER_LENGTH, "big")
                toSend += bytes(responseBody, 'ascii')

            sock.sendall(toSend)
    except:
        # TODO: unsure what to do here - what sort of errors could the system throw? we should handle each one differently
        pass

try:
    # a forever loop until client wants to exit
    while True:
        # establish connection with client
        c, addr = sock.accept()      
        print('Connected to :', addr[0], ':', addr[1])

        # start a new thread and return its identifier
        t = start_new_thread(service_connection, (c,))
        threads.append(t)
except KeyboardInterrupt:
    print("keyboard interrupt closing")
    for c in userToSocket.values:
        c.shutdown(socket.SHUT_RDWR)
        c.close()
    sock.close()