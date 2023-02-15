import grpc
from concurrent import futures
import messageservice_pb2
import messageservice_pb2_grpc
from collections import defaultdict
import socket

import sys
sys.path.append('..')
from utils import *

host, port = "0.0.0.0", "22068"
messages = defaultdict(list)
registeredUsers = set()

class MessageServer(messageservice_pb2_grpc.MessageServiceServicer):        
    def Register(self, request, context):
        username = request.username
        print(f"Received register request from {username}")
        if username in registeredUsers:
            return messageservice_pb2.StatusCodeResponse(statusCode=USERNAME_EXISTS)
        registeredUsers.add(request.username)
        return messageservice_pb2.StatusCodeResponse(statusCode=REGISTRATION_OK)
    
    def Login(self, request, context):
        username = request.username
        print(f"Received login request from {username}")
        
    def Subscribe(self, request, context):
        username = request.username
        print(f"Received subscribe request from {username}") 
   
    def Search(self, request, context):
        query = request.query
        print(f"Received search request with query {query}") 
        
    def Send(self, request, context):
        sender, receiver, message = request.sender, request.receiver, request.message
        print(f"Received send request from {sender} to {receiver} with message {message}")
    
    def Logout(self, request, context):
        username = request.username
        print(f"Received logout request from {username}") 
        
    def Delete(self, request, context):
        username = request.username
        print(f"Received delete request from {username}") 
    
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
        print("Keyboard interrupt detected, server shutting down")
        sys.exit(0)
