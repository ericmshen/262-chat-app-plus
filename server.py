import socket
from collections import defaultdict
import threading
import time
import pickle

import sys
sys.path.append('..')
from utils import *

# we maintain a relatively simple implementation: no selectors are used, with a new
# thread being opened for each client connection. All data is also stored in memory
# (so if the server exits, no data is saved). For each client connection, we loop
# while reading input, processing it, and returning an appropriate response.

# *** CONSTS *** (or variables set once during initialization)
# The server uuid: either 0, 1, or 2, and the uuid of the primary server.
SERVER_ID = -1

# listen to any incoming client connections
HOST_LISTEN_ALL = '0.0.0.0'

# store the hostnames of other servers to communicate with
SERVER_HOSTS = ["", "", ""]

# stores the indices of the other servers that this server will have to communicate with if it is the primary
OTHER_SERVERS = []

# *** VARIABLES *** (to track state of server in an easy, class-free manner)
# this server instance's streaming socket for handling client requests
clientSock = None

# this server instance's datagram socket for server-to-server communications
serverSock = None

# all relevant quantities to persist in the state, we store this via pickling and will
# load this upon system reboot.
serverState = {
    # timestamp of snapshot
    "timestamp": time.time(),
    
    # all registered users
    "registeredUsers": set(),
    
    # the message buffer stores undelivered messages, and is a dictionary mapping usernames
    # to a list of messages they are to receive upon login
    # each message is encoded as a string with the format "<sender>|<receiver>"
    "messageBuffer": defaultdict(list),
    
    # we don't need to keep track of which users are logged in - in the event that
    # the system shuts down, we automatically mark the user as logged out on both the
    # client and server code
}

# keep a list of all opened threads, to make sure they don't get GC'd (perhaps unnecessary)
threads = []

# map of active, logged in usernames to the sockets through which they are connected 
# to the server; the keys of this dictionary thus serve as a list of online users
userToSocket = {}

# helper functions to load and save state from disk 
# save the state as a pickle
# we currently have a rather inefficient implementation where the server state is saved to disk
# each time it is updated, so you'll see this being called a couple times below when handling
# client connections
def save_server_state():
    global serverState
    print(f"saving server state for ID {SERVER_ID}")
    serverState["timestamp"] = time.time()
    with open(f'state/server_{SERVER_ID}.pickle', 'wb') as f:
        pickle.dump(serverState, f)

# attempt to load the state from a pickle (if it exists)
def load_server_state():
    global serverState
    print(f"loading server state for ID {SERVER_ID}")
    try:
        with open(f"state/server_{SERVER_ID}.pickle", 'rb') as f:
            serverState = pickle.load(f)
    except:
        print("> no previous server state found")

# each individual thread runs this function to communicate with its respective client
def service_connection(clientSocket, clientAddr):
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
        # the server status of the operation
        status = UNKNOWN_ERROR
        # a reponse header used in some operations, e.g. for the length in bytes of the body
        responseHeader = None
        # the response body, whose form and length depends on the operation and status code
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
            if username in serverState["registeredUsers"]:
                print(f"{username} is already registered")
                status = REGISTER_USERNAME_EXISTS
            # register the username by adding it to registeredUsers; the user
            # is not automatically logged in
            else:
                serverState["registeredUsers"].add(username)
                save_server_state()
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
            if username in serverState["registeredUsers"]:
                # the user should not be logged in, i.e. not in userToSocket
                if username in userToSocket:
                    print(f"{username} is already logged in")
                    status = LOGIN_ALREADY_LOGGED_IN
                else:
                    # register the socket under the current user's username
                    userToSocket[username] = clientSocket
                    # on login we deliver all undelivered messages in the form of a 2-byte header
                    # indicating the number of messages to send, then the messages themselves
                    numUndelivered = len(serverState["messageBuffer"][username])
                    if numUndelivered > 0:
                        # send the number of unread messages, as well as the formatted messages,
                        # separated by newlines
                        responseHeader = numUndelivered
                        responseBody = "\n".join(serverState["messageBuffer"][username])
                        # clear the buffer for the logged in user
                        serverState["messageBuffer"][username] = []
                        save_server_state()
                        status = LOGIN_OK_UNREAD_MSG
                        print(f"{username} successfully logged in, {numUndelivered} unread message(s)")
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
            matched = searchUsernames(list(serverState["registeredUsers"]), query)
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
                    2 * DELIMITER_LENGTH )
                messageRawDecoded = messageRaw.decode('ascii').split("|")
            except: disconnect()
            sender, recipient, message = messageRawDecoded[0], messageRawDecoded[1], messageRawDecoded[2]
            # check if the recipient exists
            if recipient not in serverState["registeredUsers"]:
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
                serverState["messageBuffer"][recipient].append(f"{sender}|{message}")
                save_server_state()
                print(f"buffered message from {sender} to {recipient}")
                status = SEND_OK_BUFFERED
                
        # *** LOGOUT ***
        # server receives a username and returns a status code
        elif op == OP_LOGOUT:
            print(">> logout requested")
            # read the username
            username = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
            # this should never happen (the client should check that the username is that
            # of the user using the client, and since the client is connected, the user
            # should be logged in)
            if username not in userToSocket:
                status = UNKNOWN_ERROR
            # the username is no longer active, so its corresponding socket can be removed;
            # this is all that is needed to mark a user as logged out for the server
            else:
                del userToSocket[username]
                print(f"{username} logged out")
                status = LOGOUT_OK
            
        # *** DELETE ***
        # server receives a username and returns a status code; buffered messages from
        # the user are kept in the buffer
        elif op == OP_DELETE:
            print(">> delete requested")
            # read the username
            username = clientSocket.recv(USERNAME_LENGTH).decode('ascii')
            # this should never happen (the client should check the username corresponds
            # to that of the currently logged-in user)
            if username not in userToSocket:
                status = UNKNOWN_ERROR
            else:
                # first "logout" the user
                del userToSocket[username]
                # the username no longer exists; note one can request a delete, but register
                # again using the same username
                serverState["registeredUsers"].remove(username)
                save_server_state()
                print(f"{username} deleted")
                status = DELETE_OK
        
        # we should never get here
        else:
            print(">> unknown operation issued")
            status = BAD_OPERATION
        
        # server-to-server communication for persistence of state:
        # inform the replicas of state-changing queries that were successful so they can update their state
        # we use datagrams - see the dev journal for discussion
        stateChangingStatuses = {DELETE_OK, SEND_OK_BUFFERED, LOGIN_OK_NO_UNREAD_MSG, LOGIN_OK_UNREAD_MSG, REGISTER_OK}
        if status in stateChangingStatuses:
            update = op.to_bytes(CODE_LENGTH, "big")

            # logins: send the client address - we don't currently use the address, but this information
            # may be useful for extending implementations
            if status in {LOGIN_OK_NO_UNREAD_MSG, LOGIN_OK_UNREAD_MSG}:
                print(f"communicating client login to replicas")
                clientAddrRepr = str(clientAddr) + "|"
                update += bytes(clientAddrRepr, 'ascii')
            
            # undelievered messages: send the message contents
            if status == SEND_OK_BUFFERED:
                update += messageRaw
                
            # for registers, logins, and deletes: send the username in question
            else:
                update += bytes(username, 'ascii')

            # send this update to secondary replicas
            # we use datagrams which are lightweight but less reliable/can't detect if a connection has
            # closed: we can simply send the update to all other servers
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for replica in OTHER_SERVERS:
                print(f"sending update to replica {SERVER_HOSTS[replica]} {INTERNAL_SERVER_PORTS[replica]}")
                s.sendto(update, (SERVER_HOSTS[replica], INTERNAL_SERVER_PORTS[replica]))
                # sleep to give replicas time to update their states
                time.sleep(0.3)

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

# if the server is a replica it needs to listen for updates from the primary; this is the helper 
# function to do this, given the socket where updates are being received
def listen_for_updates(serverSock):
    # run this in a loop
    while True:
        # prepare to receive the longest message the primary could possibly send
        data, _ = serverSock.recvfrom(
            CODE_LENGTH + 
            MESSAGE_LENGTH + 
            2 * USERNAME_LENGTH + 
            2 * DELIMITER_LENGTH)

        print("received server state update")
        # check what type of state update this is
        op = data[0]

        # registers: add the user
        if op == OP_REGISTER:
            username = data[1:].decode('ascii')
            serverState["registeredUsers"].add(username)
            save_server_state()
            print(f"state update: registered user {username}")
        
        # login: clear the buffer for the user - we also send along the client address but don't
        # make use of it in our implementation as it stands
        elif op == OP_LOGIN:
            messageRawDecoded = data[1:].decode('ascii').split("|")
            _, username = messageRawDecoded[0], messageRawDecoded[1]
            serverState["messageBuffer"][username] = []
            save_server_state()
            print(f"state update: logged in user {username}")
        
        # (buffered) sends: update the message cache
        elif op == OP_SEND:
            messageRawDecoded = data[1:].decode('ascii').split("|")
            sender, recipient, message = messageRawDecoded[0], messageRawDecoded[1], messageRawDecoded[2]
            serverState["messageBuffer"][recipient].append(f"{sender}|{message}")
            save_server_state()
            print(f"state update: buffered message from {sender} to {recipient}")
            
        # deletes: remove the user
        elif op == OP_DELETE:
            username = data[1:].decode('ascii')
            serverState["registeredUsers"].remove(username)
            save_server_state()
            print(f"state update: deleted user {username}")

# function that sets up the client-to-server socket, and primes the server to listen to client
# connections across this socket
def run_server():
    global clientSock
    # put the socket into listening mode
    # start the server's own socket, bind it, and broadcast the host/port (for client connections)
    clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSock.bind((HOST_LISTEN_ALL, port))
    print(f"server socket started on host {socket.gethostname()} and port {port}")
    
    clientSock.listen(CLIENT_CAPACITY)
    print("server listening for clients...")
        
    while True:
        # attempt to establish connection with clients
        # since clients only initiate connections to the current primary, actually accepting a connection
        # means that the current server replica now becomes the primary
        try:
            c, addr = clientSock.accept()
        # gracefully-ish handle a keyboard interrupt by closing the active sockets;
        # this will also notify the clients that the server connection has ended
        except KeyboardInterrupt:
            print("\ncaught interrupt, shutting down server")
            for c in userToSocket.values():
                c.close()
            clientSock.close()
            break 
        # also simply shut down if we can't connect to a new user for some reason
        except:
            print("failed to accept socket connection, shutting down server")
            for c in userToSocket.values():
                c.close()
            clientSock.close()
            break
        print(f"connected to new client {addr[0]}:{addr[1]} - now acting as primary replica")
        
        # multithreading setup for multiple concurrent client connections:
        # start a new thread for each client connection and return its identifier
        servicer = threading.Thread(target=service_connection, args=(c, addr,))
        servicer.daemon = True
        servicer.start()
        threads.append(servicer)

if __name__ == "__main__":
    # a port can be specified when running the program
    if len(sys.argv) != 5:
        print(f"usage: {sys.argv[0]} <server ID (0, 1, 2)> <server 0 host> <server 1 host> <server 2 host>")
        sys.exit(1)
        
    # set the server's current ID, and the other servers' addresses
    SERVER_ID = int(sys.argv[1])
    SERVER_HOSTS = [sys.argv[2], sys.argv[3], sys.argv[4]]
    port = SERVER_PORTS[SERVER_ID]
    OTHER_SERVERS = list({0, 1, 2} - {SERVER_ID})
        
    # persistence: check if there is existing server state
    print(f'starting server with ID {SERVER_ID}')
    load_server_state()
    
    # set up a datagram socket to listen for updates from other servers if the server isn't currently
    # a primary replica (see design doc)
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serverSock.bind((SERVER_HOSTS[SERVER_ID], INTERNAL_SERVER_PORTS[SERVER_ID]))
    print("server internal socket started on port", INTERNAL_SERVER_PORTS[SERVER_ID])

    # start listening to other servers on another thread
    listener = threading.Thread(target=listen_for_updates, args=(serverSock,))
    listener.daemon = True
    listener.start()
    threads.append(listener)

    # set up this server's client-to-server socket too, anticipating eventual connections (when the
    # server becomes the primary replica)
    run_server()