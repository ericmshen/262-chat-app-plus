import grpc
from concurrent import futures
from messageservice_pb2 import *
import messageservice_pb2_grpc
from collections import defaultdict
import socket
from queue import Queue

import sys
sys.path.append('..')
from utils import *

host, port = "0.0.0.0", "22068"
# map of username (strings) to a list of messages they will receive when they log in
# each message is stored as a string "<sender>|<message>"
messageBuffer = defaultdict(list)
registeredUsers = set()
activeUsers = {}

class MessageServer(messageservice_pb2_grpc.MessageServiceServicer):        
    def Register(self, request, context):
        username = request.username
        print(f"received register request from {username}")
        if username in registeredUsers:
            print("username already exists")
            return StatusCodeResponse(statusCode=REGISTER_USERNAME_EXISTS)
        registeredUsers.add(request.username)
        print("registeration successful")
        return StatusCodeResponse(statusCode=REGISTER_OK)
    
    def Login(self, request, context):
        username = request.username
        print(f"received login request from {username}")
        if username not in registeredUsers:
            print("username is not registered")
            return LoginResponse(statusCode=LOGIN_NOT_REGISTERED)
        if username in activeUsers:
            print("username is already logged in")
            return LoginResponse(statusCode=LOGIN_ALREADY_LOGGED_IN)
        activeUsers[username] = Queue()
        numUndelivered = len(messageBuffer[username])
        if numUndelivered == 0:
            print("login successful, no unread messages")
            return LoginResponse(statusCode=LOGIN_OK_NO_UNREAD_MSG)
        unreadMessages = []
        for message in messageBuffer[username]:
            sender, body = message.split("|")
            unreadMessages.append(Message(sender=sender, body=body))
        print(f"login successful, {len(unreadMessages)} unread messages")
        messageBuffer[username] = []
        return LoginResponse(statusCode=LOGIN_OK_UNREAD_MSG, messages=unreadMessages)
        
    def Subscribe(self, request, context):
        username = request.username
        print(f"received subscribe request from {username}")
        while True:
            try:
                message = activeUsers[username].get()
                if message == "~EOF":
                    break
                sender, body = message.split("|")
                yield Message(sender=sender, body=body)
            except:
                print("received an unknown error getting message")
                break
        # TODO: check if this queue idea works
   
    def Search(self, request, context):
        query = request.query
        print(f"received search request with query {query}") 
        results = searchUsernames(list(registeredUsers), query)
        numResults = len(results)
        if numResults == 0:
            print(f"search executed, no results")
            return SearchResponse(statusCode=SEARCH_NO_RESULTS)
        print(f"search executed, {numResults} result(s)")
        resp = SearchResponse(statusCode=SEARCH_OK)
        resp.results.extend(results)
        return resp
        
    def Send(self, request, context):
        sender, recipient, body = request.sender, request.recipient, request.body
        print(f"received send request from {sender} to {recipient}")
        formattedMessage = f"{sender}|{body}"
        if recipient not in registeredUsers:
            print(f"{recipient} not found")
            return StatusCodeResponse(statusCode=SEND_RECIPIENT_DNE)
        if recipient not in activeUsers:
            print(f"{recipient} is not logged in, buffering message")
            messageBuffer[recipient].append(formattedMessage)
            return StatusCodeResponse(statusCode=SEND_OK_BUFFERED)
        print(f"{recipient} is logged in, sending message")
        try:
            activeUsers[recipient].put(formattedMessage)
        except:
            print("unknown error in sending message")
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        return StatusCodeResponse(statusCode=SEND_OK_DELIVERED)
    
    def Logout(self, request, context):
        userToLogout = request.username
        print(f"received logout request from {userToLogout}") 
        # this shouldn't ever happen (client-side check that user is logged in)
        if userToLogout not in activeUsers:
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        activeUsers[userToLogout].put("~EOF")
        del activeUsers[userToLogout]
        return StatusCodeResponse(statusCode=LOGOUT_OK)
        
    def Delete(self, request, context):
        userToDelete = request.username
        print(f"received delete request from {userToDelete}") 
        # this shouldn't ever happen (client-side check that user is logged in)
        if userToDelete not in registeredUsers:
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        registeredUsers.remove(userToDelete)
        activeUsers[userToDelete].put("~EOF")
        del activeUsers[userToDelete]
        del messageBuffer[userToDelete]
        return StatusCodeResponse(statusCode=DELETE_OK)
    
def serve(port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messageservice_pb2_grpc.add_MessageServiceServicer_to_server(MessageServer(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print(f"server started, listening on host {socket.gethostname()} and port {port}")
    server.wait_for_termination()

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print(f"usage: {sys.argv[0]} <optional port>")
        sys.exit(1)
    if len(sys.argv) == 2:
        port = sys.argv[1]
    
    print("starting server...")
    
    try:
        serve(port)
    except KeyboardInterrupt:
        print("\ncaught interrupt, server shutting down")
        sys.exit(0)
