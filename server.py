import socket
from collections import defaultdict
import threading

import sys
sys.path.append('..')
from utils import *

# We maintain a relatively simple implementation: no selectors are used, with a new
# thread being opened for each client connection. All data is also stored in memory
# (so if the server exits, no data is saved). For each client connection, we loop
# while reading input, processing it, and returning an appropriate response.

# *** VARIABLES *** (to track state of server in an easy, class-free manner)
# allow any incoming connections on port 22067 by default (port can be specified)
host, port = "0.0.0.0", 22067

# keep track of all registered users
registeredUsers = set()

# the message buffer stores unsent messages, and is a dictionary mapping usernames
# to a list of messages they are to receive upon login
# each message is encoded as a string with the format "<sender>|<receiver>"
messageBuffer = defaultdict(list)

# keep a list of all opened threads, to make sure they don't get GC'd (perhaps unnecessary)
threads = []

# map of active, logged in usernames to the sockets through which they are connected 
# to the server; the keys of this dictionary thus serve as a list of online users
userToSocket = {}

# each individual thread runs this function to communicate with its respective client
def service_connection(clientSocket):
    """ For each thread servicing a client connection. Over the lifetime of the connection, 
    it loops and reads from the client socket. It first reads a 1-byte operation code 
    determining the operation desired by the client (as laid out in the spec), 
    followed by operation-specific data, if applicable. It processes the request and 
    returns an operation-specific status code, along with any data to send to the client, 
    if applicable. """
    
    # helper function to disconnect a client socket and return from the thread
    def disconnect():
        print("not connected to client, closing socket")
        clientSocket.close()
        # try to log the corresponding user out if they haven't already; this usually should
        # not happen, as the client code will try to logout before ending the connection
        userToLogout = None 
        for user, sock in userToSocket:
            if sock is clientSocket:
                userToLogout = user 
                break
        if userToLogout:
            del userToSocket[userToLogout]
        return 
    
    # loop until socket closed or program interrupted; the overall message from the client
    # is an operation code followed by operation-specific data, and the overall response is 
    # a status code followed by status-specific data (the message details for a receive operation,
    # or a header that indicates length followed by a body for search and login operations)
    while True:
        # read 1 byte for the operation code
        try:
            op = clientSocket.recv(1)
        # there's an error communicating with the client: close the socket
        except: 
            disconnect()
        # if the client disconnects, it sends back a None or 0 over the socket;
        # in this case the socket should also be closed
        if not op:
            print("client disconnected, closing socket")
            clientSocket.close()
            return
        op = int.from_bytes(op, "big")
        # values to return over the socket
        status = UNKNOWN_ERROR
        responseHeader = None
        responseBody = None
        print(f"> client issued operation code {op}")

        # *** REGISTER ***
        # server receives the username and returns a status code
        if op == OP_REGISTER:
            print(">> registration requested")
            # read the username
            try:
                username = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
            except: disconnect()
            # check that the username is new
            if username in registeredUsers:
                print(f"{username} is already registered")
                status = REGISTER_USERNAME_EXISTS
            # register the username by adding it to registeredUsers; the user
            # is not automatically logged in
            else:
                registeredUsers.add(username)
                print(f"{username} successfully registered")
                status = REGISTER_OK
        
        # *** LOGIN ***
        # server receives a username and returns a status code; if the user is
        # valid and has unread messages, the server also returns the unread messages
        elif op == OP_LOGIN:
            print(">> login requested")
            # read the username
            try:
                username = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
            except: disconnect()
            if username in registeredUsers:
                # the user should not be logged in, i.e. not in userToSocket
                if username in userToSocket:
                    print(f"{username} is already logged in")
                    status = LOGIN_ALREADY_LOGGED_IN
                else:
                    # register the socket under the current user's username
                    userToSocket[username] = clientSocket
                    # on login we deliver all undelivered messages in the form of a 2-byte header
                    # indicating the number of messages to send, then the messages themselves
                    numUndelivered = len(messageBuffer[username])
                    if numUndelivered > 0:
                        print(f"{username} successfully logged in, {numUndelivered} unread message(s)")
                        status = LOGIN_OK_UNREAD_MSG
                        # send the number of unread messages, as well as the formatted messages,
                        # separated by newlines
                        responseHeader = numUndelivered
                        responseBody = "\n".join(messageBuffer[username])
                        # clear the buffer for the logged in user
                        messageBuffer[username] = []
                    else:
                        print(f"{username} successfully logged in, no unread messages")
                        status = LOGIN_OK_NO_UNREAD_MSG
            # the provided username is invalid
            else:
                print(f"{username} is not registered")
                status = LOGIN_NOT_REGISTERED
                
        # *** SEARCH ***
        # server recieves a query and returns a status code, with results if any
        elif op == OP_SEARCH:
            print(">> search requested")
            # read the query and search for it (query length cannot exceed username length)
            try:
                query = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
            except: disconnect()
            matched = searchUsernames(list(registeredUsers), query)
            if matched:
                # send back data in the form of a 2-byte header describing the number of 
                # results, then the results themselves separated by |
                responseHeader = len(matched)
                responseBody = "|".join(matched)
                print(f"search executed, {responseHeader} result(s)")
                status = SEARCH_OK
            # query doesn't match anything
            else:
                print(f"search executed, no results")
                status = SEARCH_NO_RESULTS
                
        # *** SEND ***
        # server receives a sender, receiver, and message, and does two things:
        # the server sends the sender username and message to the intended reciever if 
        # they are logged in using the corresponding socket (message is buffered 
        # otherwise); the server also returns a status code to the sender, except for 
        # the case where the sender and receiver are the same
        elif op == OP_SEND:
            print(">> send requested")
            # data is formatted as <sender username>|<receiver username>|<message>
            try:
                messageRaw = clientSocket.recv(
                    MESSAGE_LENGTH + 
                    2 * USERNAME_LENGTH + 
                    2 * DELIMITER_LENGTH ).decode('ascii').split("|")
            except: disconnect()
            sender, recipient, message = messageRaw[0], messageRaw[1], messageRaw[2]
            # check if the recipient exists
            if recipient not in registeredUsers:
                print(f"recipient {recipient} not found")
                status = SEND_RECIPIENT_DNE
            # check if the recipient is logged in, and if so deliver instantaneously
            # note that the recipient receives data encoded as the RECEIVE_OK status
            # code followed by a string <sender>|<message>; we handle returning a status
            # code to the sender client at the end of this function
            elif recipient in userToSocket:
                try:
                    userToSocket[recipient].sendall(
                        RECEIVE_OK.to_bytes(1, "big") +
                        bytes(f"{sender}|{message}", 'ascii')
                    )
                    print(f"sent message from {sender} to {recipient}")
                    # if the sender is the same as the recipient, don't send any confirmation;
                    # the user who messaged themselves need not see more than their own message
                    if sender == recipient:
                        continue 
                    status = SEND_OK_DELIVERED
                except:
                    # somehow the recipient connection was not open; try to close it
                    print(f"error sending to {recipient} socket")
                    userToSocket[recipient].close()
                    status = SEND_FAILED
            # otherwise, store the message in the buffer's reciever slot as
            # <sender>|<message>, and communicate the message's storage
            else:
                print(f"buffered message from {sender} to {recipient}")
                messageBuffer[recipient].append(f"{sender}|{message}")
                status = SEND_OK_BUFFERED
                
        # *** LOGOUT ***
        # server receives a username and returns a status code
        elif op == OP_LOGOUT:
            print(">> logout requested")
            # read the username
            userToLogout = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
            # this should never happen (the client should check that the username is that
            # of the user using the client, and since the client is connected, the user
            # should be logged in)
            if userToLogout not in userToSocket:
                status = UNKNOWN_ERROR
            # the username is no longer active, so its corresponding socket can be removed;
            # this is all that is needed to mark a user as logged out for the server
            else:
                del userToSocket[userToLogout]
                print(f"{userToLogout} logged out")
                status = LOGOUT_OK
            
        # *** DELETE ***
        # server receives a username and returns a status code; buffered messages from
        # the user are kept in the buffer
        elif op == OP_DELETE:
            print(">> delete requested")
            # read the username
            userToDelete = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
            # this should never happen (the client should check the username corresponds
            # to that of the currently logged-in user)
            if userToDelete not in userToSocket:
                status = UNKNOWN_ERROR
            else:
                # first "logout" the user
                del userToSocket[userToDelete]
                # the username no longer exists; note one can request a delete, but register
                # again using the same username
                registeredUsers.remove(userToDelete)
                print(f"{userToDelete} deleted")
                status = DELETE_OK
        
        # we should never get here
        else:
            print(">> unknown operation issued")
            status = BAD_OPERATION
        
        # the server's response to the original client will ALWAYS consist of a 1-byte status 
        # code, followed by a response header and body if any
        toSend = status.to_bytes(CODE_LENGTH, "big")
        # the protocol is such that there will either be BOTH a response header and body or neither; 
        # the header just indicates the length (# of messages/results) in the body so that the client
        # knows how many bytes to read (possible in the login and search operations)
        # one exception to this is when a client is RECEIVING messages, which simply contain 
        # the RECEIVE_OK code followed by the sender and receiver; however, that's not returned
        # to the client MAKING the request, which is what we consider here
        if responseHeader and responseBody:
            toSend += responseHeader.to_bytes(MSG_HEADER_LENGTH, "big")
            toSend += bytes(responseBody, 'ascii')
        clientSocket.sendall(toSend)
        print("server response given")

if __name__ == "__main__":
    # a port can be specified when running the program
    if len(sys.argv) > 2:
        print(f"usage: {sys.argv[0]} <optional port>")
        sys.exit(1)
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
        
    print('starting server...')
    
    # start the socket, bind it, and broadcast the host/port (for client connections)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    print(f"server started, listening on host {socket.gethostname()} and port {port}")

    # put the socket into listening mode
    sock.listen(10)
    print("server is listening")

    # a forever loop until program exit
    while True:
        # establish connection with client
        try:
            # a future extension: add timeouts to connections
            c, addr = sock.accept()
        # gracefully-ish handle a keyboard interrupt by closing the active sockets;
        # this will also notify the clients that the server connection has ended
        except KeyboardInterrupt:
            print("\ncaught interrupt, shutting down server")
            for c in userToSocket.values():
                c.close()
            sock.close()
            break 
        # also simply shut down if we can't connect to a new user for some reason
        except:
            print("failed to accept socket connection, shutting down server")
            for c in userToSocket.values():
                c.close()
            sock.close()
            break
        print(f"connected to new client {addr[0]}:{addr[1]}")

        # multithreading setup for multiple concurrent client connections:
        # start a new thread for each client connection and return its identifier
        servicer = threading.Thread(target=service_connection, args=(c,))
        servicer.daemon = True
        servicer.start()
        threads.append(servicer)
