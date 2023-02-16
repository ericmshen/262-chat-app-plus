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
# TODO: map to a queue or something
activeUsers = {}

class MessageServer(messageservice_pb2_grpc.MessageServiceServicer):        
    def Register(self, request, context):
        username = request.username
        print(f"Received register request from {username}")
        if username in registeredUsers:
            print("Username already exists!")
            return StatusCodeResponse(statusCode=REGISTER_USERNAME_EXISTS)
        registeredUsers.add(request.username)
        print("Registeration successful")
        return StatusCodeResponse(statusCode=REGISTER_OK)
    
    def Login(self, request, context):
        username = request.username
        print(f"Received login request from {username}")
        if username not in registeredUsers:
            print("Username is not registered!")
            return LoginResponse(statusCode=LOGIN_NOT_REGISTERED)
        if username in activeUsers:
            print("Username is already logged in!")
            return LoginResponse(statusCode=LOGIN_ALREADY_LOGGED_IN)
        activeUsers[username] = Queue()
        numUndelivered = len(messageBuffer[username])
        if numUndelivered == 0:
            print("Login successful, no unread messages")
            return LoginResponse(statusCode=LOGIN_OK_NO_UNREAD_MSG)
        unreadMessages = []
        for message in messageBuffer[username]:
            sender, body = message.split("|")
            unreadMessages.append(Message(sender=sender, body=body))
        print(f"Login successful, {len(unreadMessages)} unread messages")
        return LoginResponse(statusCode=LOGIN_OK_UNREAD_MSG, messages=unreadMessages)
        
    def Subscribe(self, request, context):
        username = request.username
        print(f"Received subscribe request from {username}")
        while True:
            try:
                message = activeUsers[username].get()
                if message == "~EOF":
                    return
                sender, body = message.split("|")
                yield Message(sender=sender, body=body)
            except:
                print("Received an unknown error getting message!")
                break
        # TODO: some queue shit
   
    def Search(self, request, context):
        query = request.query
        print(f"Received search request with query {query}") 
        results = searchUsernames(list(registeredUsers), query)
        if len(results) == 0:
            return SearchResponse(statusCode=SEARCH_NO_RESULTS)
        resp = SearchResponse(statusCode=SEARCH_OK)
        resp.results.extend(results)
        return resp
        
    def Send(self, request, context):
        sender, receiver, body = request.sender, request.receiver, request.body
        print(f"Received send request from {sender} to {receiver} with message {body}")
        formattedMessage = f"{sender}|{body}"
        if receiver not in activeUsers:
            print("Receiver is not logged in, buffering message")
            messageBuffer[receiver].append(formattedMessage)
            return StatusCodeResponse(statusCode=SEND_OK_BUFFERED)
        print("Receiver is logged in, sending message")
        try:
            activeUsers[receiver].put(formattedMessage)
        except:
            print("Unknown error in sending message!")
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        return StatusCodeResponse(statusCode=SEND_OK_DELIVERED)
    
    def Logout(self, request, context):
        username = request.username
        print(f"Received logout request from {username}") 
        # this shouldn't ever happen (client-side check that user is logged in)
        if username not in activeUsers:
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        activeUsers[username].put("~EOF")
        del activeUsers[username]
        return StatusCodeResponse(statusCode=LOGOUT_OK)
        
    def Delete(self, request, context):
        username = request.username
        print(f"Received delete request from {username}") 
        # this shouldn't ever happen (client-side check that user is logged in)
        if username not in registeredUsers:
            return StatusCodeResponse(statusCode=UNKNOWN_ERROR)
        registeredUsers.remove(username)
        # TODO: push some EOF message to the queue first?
        activeUsers[username].put("~EOF")
        del activeUsers[username]
        del messageBuffer[username]
        # option: modify the message dictionary?
        # for user, messageList in messages:
        #     newList = []
        #     for message in messageList:
        #         sender, body = message.split("|")
        #         if sender == username:
        #             message = f"<deleted user>|{body}"
        #     newList.append(message)
        #     messages[user] = newList
        return StatusCodeResponse(statusCode=DELETE_OK)
    
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messageservice_pb2_grpc.add_MessageServiceServicer_to_server(MessageServer(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print(f"Server started, listening on host {socket.gethostname()} and port {port}")
    server.wait_for_termination()

if __name__ == '__main__':
    try:
        serve()
    except KeyboardInterrupt:
        print("\nCaught interrupt, server shutting down")
        sys.exit(0)
