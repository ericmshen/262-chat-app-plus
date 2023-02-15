import grpc
from messageservice_pb2 import *
import messageservice_pb2_grpc
import sys

def run(stub:messageservice_pb2_grpc.MessageServiceStub):
    pass

def test(stub:messageservice_pb2_grpc.MessageServiceStub):
    # test send message
    print("Sending invalid login...")
    response = stub.Login(UsernameRequest(username="poo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending register...")
    response = stub.Register(UsernameRequest(username="poo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending re-register...")
    response = stub.Register(UsernameRequest(username="poo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending login...")
    response = stub.Login(UsernameRequest(username="poo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending invalid login...")
    response = stub.Login(UsernameRequest(username="poopy balls"))
    print(f"Client received status code: {response.statusCode}")

def startClient():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <host>")
        sys.exit(1)
    host = sys.argv[1]
    port = "22068"
    
    print("Starting gRPC client...")
    
    with grpc.insecure_channel(host + ":" + port) as channel:
        print(f"Connected to {host}:{port}")
        stub = messageservice_pb2_grpc.MessageServiceStub(channel)
        run(stub)

if __name__ == '__main__':
    startClient()
