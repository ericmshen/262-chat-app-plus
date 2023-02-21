import grpc
from messageservice_pb2 import *
import messageservice_pb2_grpc
import threading

import sys
sys.path.append('..')
from utils import *

# username of the logged in user on the client side: if None, no user is logged in
# we use this to detect if the client code has someone logged in or not
username = None

# a helper function that is read from a stream of messages, formatting and printing them
# as they arrive; run in a separate thread to avoid blocking
def listenForMessages(messageStream):
    for message in messageStream:
        print(f"{message.sender}: {message.body}")

# TODO: gracefully handle server shutdown, or unavailable server

def serve(stub:messageservice_pb2_grpc.MessageServiceStub):
    """Given a gRPC stub, handles all client interaction with the server. Over the lifetime
    of the connection, repeatedly prompts for user input, processes entered data, communicates
    with the server, and prints results."""
    
    global username
    
    # TODO: for convenience, can first ping stub to see if server is online
    # TODO: try catch everything
    print(">> type a command to begin: {register, login, search, send, logout, delete, quit}")
    
    # loop until socket closed or program interrupted
    while True:
        # the first input is the desired operation
        command = input("").lower().strip()
        if command not in commandToOpcode:
            print("<< please type an actual command")
            continue
        # find the operation code and handle based on that
        opcode = commandToOpcode[command]
        
        # *** REGISTER ***
        if opcode == OP_REGISTER:
            # can't do this if you're already logged in
            if username:
                print(f"<< you are already logged in as {username}, please logout and try again")
                continue
            # prompt the user for their username
            usernameInput = input(">> please enter username: ").strip()
            # client side check for valid username
            if not isValidUsername(usernameInput):
                print("<< usernames may not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            # send the registration request to the server and handle the response
            # don't "login" (set the username) yet; the user should explicitly login
            response = stub.Register(UsernameRequest(username=usernameInput))
            if response.statusCode == REGISTER_OK:
                print(f"<< {usernameInput} successfully registered, please login")
            elif response.statusCode == REGISTER_USERNAME_EXISTS:
                print(f"<< {usernameInput} is already registered, please login")
            else:
                print("unexpected response from server")
                
        # *** LOGIN ***
        elif opcode == OP_LOGIN:
            # # can't do this if you're already logged in
            if username:
                print(f"<< you are already logged in as {username}, please logout and try again")
                continue
            # prompt the user for their username
            usernameInput = input(">> please enter username: ").strip()
            # client side check for valid username
            if not isValidUsername(usernameInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            # send the login request to the server and handle the response
            response = stub.Login(UsernameRequest(username=usernameInput))
            # with successful status codes LOGIN_OK_NO_UNREAD_MSG and LOGIN_OK_UNREAD_MSG,
            # automatically call Subscribe to listen for new incoming messages; this call will
            # live in a new thread and will be responsible for instantly printing messages
            if response.statusCode == LOGIN_OK_NO_UNREAD_MSG:
                username = usernameInput
                print(f"<< welcome {username}, you have no new messages")
                # create a message stream from the Subscribe call and pass it to a thread
                newMessageStream = stub.Subscribe(UsernameRequest(username=username)) 
                listener = threading.Thread(target=listenForMessages, args=(newMessageStream,))
                listener.daemon = True
                listener.start()
            elif response.statusCode == LOGIN_OK_UNREAD_MSG:
                username = usernameInput
                # receive and print the actual messages
                unreadMessages = response.messages
                numMessages = len(unreadMessages)
                if numMessages == 1:
                    print(f"<< welcome {username}, you have one new message:")
                else:
                    print(f"<< welcome {username}, you have {numMessages} new messages:")
                for message in unreadMessages:
                    print(f"{message.sender}: {message.body}")
                # create a message stream from the Subscribe call and pass it to a thread
                newMessageStream = stub.Subscribe(UsernameRequest(username=username)) 
                listener = threading.Thread(target=listenForMessages, args=(newMessageStream,))
                listener.daemon = True
                listener.start()
            # if there's an error, don't set the username variable
            elif response.statusCode == LOGIN_NOT_REGISTERED:
                print(f"<< {usernameInput} is not registered. please register before logging in")
            elif response.statusCode == LOGIN_ALREADY_LOGGED_IN:
                print(f"<< {usernameInput} is already logged in")
            else:
                print("<< unexpected response from server")
        
        # *** SEARCH ***
        elif opcode == OP_SEARCH:
            # prompt the user for the search query, client-side check for validity
            query = input(">> enter query: ").strip()
            if not isValidQuery(query):
                print("<< search queries must not be blank, must be under 50 characters, and must be comprised of alphanumerics and wildcards (*), please try again")
                continue
            # send the query to the server
            response = stub.Search(SearchRequest(query=query))
            if response.statusCode == SEARCH_OK:
                # print the results
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
                
        # *** SEND ***
        elif opcode == OP_SEND:
            # can't send if you're not logged in
            if not username:
                print(">> you must be logged in to send a message")
                continue
            # read the receiver username and then the message; client-side checks for validity
            recipient = input(">> username of recipient: ").strip()
            if not isValidUsername(recipient):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            message = input(">> message: ").strip()
            if not isValidMessage(message):
                print(f"<< messages must contain only ASCII (English) characters, not contain newlines or '|', must not be blank, and must be under 262 characters (current length {len(message)} characters), please try again")
                continue
            # send the sender, recipient, and message to the server, and interpret response
            response = stub.Send(MessageRequest(sender=username, recipient=recipient, body=message))
            if response.statusCode == SEND_OK_DELIVERED:
                print(f"<< message delivered to {recipient}")
            elif response.statusCode == SEND_OK_BUFFERED:
                print(f"<< your message to {recipient} will be delivered when they log in")
            elif response.statusCode == SEND_RECIPIENT_DNE:
                print(f"<< the user {recipient} does not exist, or has deleted their account")
            else:
                print("<< unexpected response from server")
        
        # *** LOGOUT AND DELETE ***
        elif opcode in { OP_LOGOUT, OP_DELETE }:
            # can't do either operation if you're not logged in
            if not username:
                print("<< you are not logged in to an account")
                continue
            # like register and search, take in the username as a confirmation step, client-side
            # check for validity
            usernameInput = input(f">> enter username to confirm {command}: ").strip()
            if not isValidUsername(usernameInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            if usernameInput != username:
                print("<< the username typed does not match your username, please try again")
                continue
            # send the username to the server, with Logout or Delete call
            if opcode == OP_LOGOUT:
                response = stub.Logout(UsernameRequest(username=username))
                if response.statusCode == LOGOUT_OK:
                    print("<< successfully logged out")
                    username = None
                else:
                    print("<< unexpected response from server")
            else:
                response = stub.Delete(UsernameRequest(username=username))
                if response.statusCode == DELETE_OK:
                    print("<< succesfully logged out and deleted account")
                    username = None
                else:
                    print("<< unexpected response from server")
        # only OP_DISCONNECT commands remain: "bye", "disconnect", "quit"
        # logic is already handled in KeyboardInterrupt exception handling
        else: 
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
    """Sets up and handles the client gRPC connection."""
    global username 
    
    # must specify a host and port to connect to
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)
    host, port = sys.argv[1], sys.argv[2]
    
    print("starting gRPC client...")
    
    # for our purposes we only need an insecure connection
    # using the "with" keyword allows us to have python manage the work around
    # manually closing channels
    with grpc.insecure_channel(host + ":" + port) as channel:
        print(f"starting connection to {host}:{port}")
        # create the stub
        stub = messageservice_pb2_grpc.MessageServiceStub(channel)
        try:
            serve(stub)
        # upon an interrupt, logout if there's a user currently logged in, then exit
        except KeyboardInterrupt:
            print("\n<< caught interrupt, shutting down connection")
            if username:
                print(f"automatically logging out")
                stub.Logout(UsernameRequest(username=username))
                username = None
            sys.exit(0)

if __name__ == '__main__':
    startClient()
