import grpc
from concurrent import futures
from messageservice_pb2 import *
import messageservice_pb2_grpc
from collections import defaultdict
import socket
from queue import Queue
import os

import sys
sys.path.append('..')
from utils import *

# gRPC's functionality helps us abstract away a few details compared to sockets: handling
# threading, managing connections, etc. It allows us to write things in an arguably more
# straightforward way, similar to an API implementation. 
# 
# However, because we don't have a mapping of users to sockets and data is transfered through 
# server calls, the way we send messages instantly is worked a bit differently: in addition 
# to a buffer, for real-time messaging we maintain a map from users to Queues. When a user 
# logs in, they will immediately "Subscribe" to a stream of messages, wherein the server reads
# from the Queue and yields incoming messages as they arrive. Queues are closed (e.g. upon logouts)
# by passing in a special EOF string.
#
# We don't use gRPC contexts or innate status codes for simplicity.

# *** VARIABLES *** (to track state of server in an easy, class-free manner)
# allow any incoming connections on port 22068 by default (port can be specified)
host, port = "0.0.0.0", "22068"

# string to indicate that a Queue can be closed (no more messages will come through it)
QUEUE_EOF = "~EOF"

# keep track of all registered users
registeredUsers = set()

# map of username (strings) to a list of messages they will receive when they log in
# each message is stored as a string "<sender>|<message>"
messageBuffer = defaultdict(list)

# map of logged-in users to Queues to facilitate instant message sending; if a message
# is sent to a logged-in user, it is passed into its Queue, where a Subscribe() call will
# recieve it and send it; messages are formatted as "<sender>|<message>"
activeUsers = {}

# the gRPC server object
server = None

class MessageServer(messageservice_pb2_grpc.MessageServiceServicer):        
    def Register(self, request, context):
        """Registers a new user with the server. Given a UsernameRequest, the server 
        returns a StatusCodeResponse."""
        username = request.username
        print(f">> registration requested from {username}")
        # check that the username is new
        if username in registeredUsers:
            print(f"{username} is already registered")
            return StatusCodeResponse(statusCode=REGISTER_USERNAME_EXISTS)
        # register the username by adding it to registeredUsers; the user
        # is not automatically logged in
        registeredUsers.add(request.username)
        print(f"{username} successfully registered")
        return StatusCodeResponse(statusCode=REGISTER_OK)
    
    def Login(self, request, context):
        """Logs a user in. Given a UsernameRequest, the server returns a LoginResponse 
        which comprises a status code and a list of unread Messages, if any."""
        username = request.username
        print(f">> login requested from {username}")
        # check if the provided username is valid
        if username not in registeredUsers:
            print(f"{username} is not registered")
            return LoginResponse(statusCode=LOGIN_NOT_REGISTERED)
        # the user should not be logged in, i.e. not in activeUsers
        if username in activeUsers:
            print(f"{username} is already logged in")
            return LoginResponse(statusCode=LOGIN_ALREADY_LOGGED_IN)
        # initialize a new Queue object corresponding to the user in the activeUsers map:
        # messages will be inserted into this Queue to be read and sent to the user
        activeUsers[username] = Queue()
        # check for unread messages
        numUndelivered = len(messageBuffer[username])
        if numUndelivered == 0:
            print(f"{username} successfully logged in, no unread messages")
            return LoginResponse(statusCode=LOGIN_OK_NO_UNREAD_MSG)
        unreadMessages = []
        # read all the messages in the buffer and format them as Message messages
        for message in messageBuffer[username]:
            sender, body = message.split("|")
            unreadMessages.append(Message(sender=sender, body=body))
        print(f"{username} successfully logged in, {numUndelivered} unread message(s)")
        # clear the buffer and send the LoginResponse
        messageBuffer[username] = []
        return LoginResponse(statusCode=LOGIN_OK_UNREAD_MSG, messages=unreadMessages)
        
    def Subscribe(self, request, context):
        """Subscribe a user to receive messages that are delivered instantly. 
        Automatically called upon a successful login. Given a UsernameRequest, the
        server returns a stream of Messages."""
        username = request.username
        print(f">> received subscribe request from {username}")
        # loop until program exit or the Queue is given a QUEUE_EOF
        while True:
            try:
                # poll for new messages, and send if there are any
                message = activeUsers[username].get()
                if message == QUEUE_EOF:
                    break
                sender, body = message.split("|")
                print(f"sent message from {sender} to {username}")
                yield Message(sender=sender, body=body)
            except:
                print("received an unknown error getting message")
                break
   
    def Search(self, request, context):
        """Search for usernames with wildcard search. Given a SearchRequest, the server
        returns a list of strings of usernames that match the search."""
        query = request.query
        print(f">> search requested with query {query}") 
        # call the search helper function using the provided query
        results = searchUsernames(list(registeredUsers), query)
        numResults = len(results)
        # query doesn't match anything
        if numResults == 0:
            print(f"search executed, no results")
            return SearchResponse(statusCode=SEARCH_NO_RESULTS)
        print(f"search executed, {numResults} result(s)")
        # return the results
        resp = SearchResponse(statusCode=SEARCH_OK)
        resp.results.extend(results)
        return resp
        
    def Send(self, request, context):
        """Send a message. Given a MessageRequest, the server returns a StatusCodeResponse to
        the original sender. The server also sends the message to the recipient through the
        Subscribe call if they are logged in, and stores it in the buffer otherwise."""
        sender, recipient, body = request.sender, request.recipient, request.body
        print(f">> send requested from {sender} to {recipient}")
        # format the message as "<sender>|<message>" to be sent over the Queue or stored
        # in the buffer
        formattedMessage = f"{sender}|{body}"
        # check if the recipient exists
        if recipient not in registeredUsers:
            print(f"recipient {recipient} not found")
            return StatusCodeResponse(statusCode=SEND_RECIPIENT_DNE)
        # check if the recipient is logged in: if not, buffer it
        if recipient not in activeUsers:
            print(f"buffered message from {sender} to {recipient}")
            messageBuffer[recipient].append(formattedMessage)
            return StatusCodeResponse(statusCode=SEND_OK_BUFFERED)
        try:
            # add the message into the 
            print(f"queueing message from {sender} to {recipient}")
            activeUsers[recipient].put(formattedMessage)
        except:
            print("unknown error in sending message")
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        return StatusCodeResponse(statusCode=SEND_OK_DELIVERED)
    
    def Logout(self, request, context):
        """Logs a user out. Given a UsernameRequest, the server returns a StatusCodeResponse."""
        userToLogout = request.username
        print(f">> logout requested from {userToLogout}") 
        # this shouldn't ever happen (client-side check that user is logged in)
        if userToLogout not in activeUsers:
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        # close the queue and remove the user from activeUsers; this is all that is 
        # needed to mark a user as logged out for the server
        activeUsers[userToLogout].put(QUEUE_EOF)
        del activeUsers[userToLogout]
        print(f"{userToLogout} logged out")
        return StatusCodeResponse(statusCode=LOGOUT_OK)
        
    def Delete(self, request, context):
        """Logout and delete a user. Given a UsernameRequest, the server returns a 
        StatusCodeResponse. Buffered messages from the user are kept in the buffer."""
        userToDelete = request.username
        print(f">> delete requested from {userToDelete}") 
        # this shouldn't ever happen (client-side check that user is logged in)
        if userToDelete not in registeredUsers:
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        # close the queue and remove the user from activeUsers; this is all that is 
        # needed to mark a user as logged out for the server
        activeUsers[userToDelete].put(QUEUE_EOF)
        del activeUsers[userToDelete]
        # the username no longer exists
        registeredUsers.remove(userToDelete)
        del messageBuffer[userToDelete]
        print(f"{userToDelete} deleted")
        return StatusCodeResponse(statusCode=DELETE_OK)
    
def serve(port):
    global server
    """Function to set up the gRPC server."""
    # initialize the gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messageservice_pb2_grpc.add_MessageServiceServicer_to_server(MessageServer(), server)
    # for our purposes we only need an insecure connection
    server.add_insecure_port('[::]:' + port)
    server.start()
    # broadcast the host/port (for client connections)
    print(f"server started, listening on host {socket.gethostname()} and port {port}")
    server.wait_for_termination()

if __name__ == '__main__':
    # a port can be specified when running the program
    if len(sys.argv) > 2:
        print(f"usage: {sys.argv[0]} <optional port>")
        sys.exit(1)
    if len(sys.argv) == 2:
        port = sys.argv[1]
    
    print("starting server...")
    
    try:
        serve(port)
    # upon an interrupt, stop the server
    except KeyboardInterrupt:
        print("\ncaught interrupt, server shutting down")
        server.stop(0)
        os._exit(0)
