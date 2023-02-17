import grpc
from messageservice_pb2 import *
import messageservice_pb2_grpc

import sys
sys.path.append('..')
from utils import *

username = None

def serve(stub:messageservice_pb2_grpc.MessageServiceStub):
    global username
    print(">> type a command to begin: {register, login, search, send, logout, delete, quit}")
    while True:
        command = input("").lower().strip()
        if command not in commandToOpcode:
            print("<< please type an actual command")
            continue
        opcode = commandToOpcode[command]
        if opcode == OP_REGISTER:
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
        elif opcode == OP_LOGIN:
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
                print(f"<< welcome {username}, you have no new messages")
                newMessageStream = stub.Subscribe(UsernameRequest(username=username)) 
                for message in newMessageStream:
                    print(f"{message.sender}: {message.body}")
            elif response.statusCode == LOGIN_OK_UNREAD_MSG:
                username = usernameInput
                unreadMessages = response.messages
                numMessages = len(unreadMessages)
                if numMessages == 1:
                    print(f"<< welcome {username}, you have one new message:")
                else:
                    print(f"<< welcome {username}, you have {numMessages} new messages:")
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
                print("<< unexpected response from server")
        elif opcode == OP_SEARCH:
            query = input(">> enter query: ").strip()
            if not isValidQuery(query):
                print("<< search queries must not be blank, must be under 50 characters, and must be comprised of alphanumerics and wildcards (*), please try again")
                continue
            response = stub.Search(SearchRequest(query=query))
            if response.statusCode == SEARCH_OK:
                results = response.results
                numResults = len(results)
                if numResults == 1:
                    print("<< 1 username matched your query:")
                else:
                    print(f"<< {numResults} usernames matched your query:")
                for user in results:
                    print(user)
            elif response.statusCode == SEARCH_NO_RESULTS:
                print("<< no usernames matched your query")
            else:
                print("<< unexpected response from server")
        elif opcode == OP_SEND:
            if not username:
                print(">> you must be logged in to send a message")
                continue
            recipient = input(">> username of recipient: ").strip()
            if not isValidUsername(recipient):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            message = input(">> message: ").strip()
            if not isValidMessage(message):
                print("<< messages must contain only ASCII (English) characters, not contain newlines or '|', must not be blank, and must be under 262 characters, please try again")
                continue
            response = stub.Send(MessageRequest(sender=username, recipient=recipient, body=message))
            if response.statusCode == SEND_OK_DELIVERED:
                print(f"<< message delivered to {recipient}")
            elif response.statusCode == SEND_OK_BUFFERED:
                print(f"<< your message to {recipient} will be delivered when they log in")
            elif response.statusCode == SEND_RECIPIENT_DNE:
                print(f"<< the user {recipient} does not exist, or has deleted their account")
            else:
                print("<< unexpected response from server")
        elif opcode in { OP_LOGOUT, OP_DELETE }:
            if not username:
                print("<< you are not logged in to an account")
                continue
            usernameInput = input(f">> enter username to confirm logout: ").strip()
            if not isValidUsername(usernameInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            if usernameInput != username:
                print("<< the username typed does not match your username, please try again")
                continue
            if opcode == OP_LOGOUT:
                response = stub.Logout(UsernameRequest(username=username))
                if response.statusCode == LOGOUT_OK:
                    print("<< successfully logged out")
                    username = None
                else:
                    print("<< unexpected response from server")
            else:
                response = stub.Delete(UsernameRequest(username=username))
                if response.statusCode == LOGOUT_OK:
                    print("<< succesfully logged out and deleted account")
                    username = None
                else:
                    print("<< unexpected response from server")
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
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)
    host, port = sys.argv[1], sys.argv[2]
    
    print("starting gRPC client...")
    
    with grpc.insecure_channel(host + ":" + port) as channel:
        print(f"starting connection to {host}:{port}")
        stub = messageservice_pb2_grpc.MessageServiceStub(channel)
        try:
            serve(stub)
        except KeyboardInterrupt:
            print("\n<< caught interrupt, shutting down connection")
            if username:
                print(f"automatically logging out")
                stub.Logout(UsernameRequest(username=username))
                username = None
            sys.exit(0)

if __name__ == '__main__':
    startClient()
