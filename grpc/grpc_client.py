import grpc
from messageservice_pb2 import *
import messageservice_pb2_grpc

import sys
sys.path.append('..')
from utils import *

username = None
recipient = None
query = None

def run(stub:messageservice_pb2_grpc.MessageServiceStub):
    while True:
        query = input("").lower().strip()
        if query not in commandToInt:
            print("<< please type an actual command")
            continue
        queryInt = commandToInt[query]
        if queryInt == REGISTER:
            if username:
                print(f"<< you are already logged in as {username}, please logout and try again")
                continue
            username_ = input(">> please enter username: ").strip()
            if not isValidUsername(username_):
                print("<< usernames may not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            response = stub.Register(UsernameRequest(username=username_))
            

def test(stub:messageservice_pb2_grpc.MessageServiceStub):
    # test send message
    print("Sending invalid login...")
    response = stub.Login(UsernameRequest(username="foo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending register...")
    response = stub.Register(UsernameRequest(username="foo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending re-register...")
    response = stub.Register(UsernameRequest(username="foo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending login...")
    response = stub.Login(UsernameRequest(username="foo"))
    print(f"Client received status code: {response.statusCode}")
    print("Sending invalid login...")
    response = stub.Login(UsernameRequest(username="bar"))
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
        try:
            run(stub)
        except KeyboardInterrupt:
            print("\nCaught interrupt, exiting")
            sys.exit(0)

if __name__ == '__main__':
    startClient()
