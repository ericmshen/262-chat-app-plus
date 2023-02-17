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
    global username
    while True:
        query = input("").lower().strip()
        if query not in commandToOpcode:
            print("<< please type an actual command")
            continue
        queryInt = commandToOpcode[query]
        if queryInt == OP_REGISTER:
            if username:
                print(f"<< you are already logged in as {username}, please logout and try again")
                continue
            usernameInput = input(">> please enter username: ").strip()
            if not isValidUsername(usernameInput):
                print("<< usernames may not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            response = stub.Register(UsernameRequest(username=usernameInput))
            if response.statusCode == REGISTER_OK:
                print(f"<< {username} is already registered, please login")
            elif response.statusCode == REGISTER_USERNAME_EXISTS:
                print(f"<< {username} successfully registered, please login")
            else:
                print("unexpected response from server")
        elif queryInt == OP_LOGIN:
            if username:
                print(f"<< you are already logged in as {username}, please logout and try again")
                continue
            usernameInput = input(">> please enter username: ").strip()
            if not isValidUsername(usernameInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            response = stub.Login(UsernameRequest(username=usernameInput))
            if response.statusCode == LOGIN_OK_NO_UNREAD_MSG:
                username = usernameInput
                print(f"welcome {username}, you have no new messages")
                newMessageStream = stub.Subscribe(UsernameRequest(username=username)) 
                for message in newMessageStream:
                    print(f"{message.sender}: {message.body}")
            elif response.statusCode == LOGIN_OK_UNREAD_MSG:
                username = usernameInput
                unreadMessages = response.messages
                numMessages = len(unreadMessages)
                if numMessages == 1:
                    print(f"welcome {username}, you have one new message:")
                else:
                    print(f"welcome {username}, you have {numMessages} new messages:")
                for message in unreadMessages:
                    print(f"{message.sender}: {message.body}")
                newMessageStream = stub.Subscribe(UsernameRequest(username=username)) 
                for message in newMessageStream:
                    print(f"{message.sender}: {message.body}")
            elif response.statusCode == LOGIN_NOT_REGISTERED:
                print(f"<< {username} is not registered. please register before logging in")
            elif response.statusCode == LOGIN_ALREADY_LOGGED_IN:
                print(f"<< {username} is already logged in")
            else:
                print("unexpected response from server")
        elif queryInt == OP_SEARCH:
            pass
        elif queryInt == OP_SEND:
            pass 
        elif queryInt == OP_LOGOUT:
            pass 
        elif queryInt == OP_DELETE:
            pass
        else: # only OP_DISCONNECT commands remain: "bye", "disconnect", "quit"
        # logic is already handled in KeyboardInterrupt exception handling
            raise KeyboardInterrupt
            
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
