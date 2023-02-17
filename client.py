import sys
import socket
from utils import *
import threading
import os
from time import sleep

# Username of the logged in user on the client code. If None, no user is logged in.
# We use this as a proxy for detecting if the client code has someone logged in or not.
username = None

# Empty variable for specifying recipient.
recipient = None

# Connected socket.
sock = None

def listen():
    global username
    while True:
        # get the operation code and decode it into a 1 byte integer
        try:
            code = sock.recv(CODE_LENGTH)
            code = int.from_bytes(code, "big")
        # there's an error communicating with the server
        except:
            print("not connected to server, exiting client")
            sock.close()
            # quit the program
            os._exit(0)
        # if the server disconnects, it sends back a None or 0
        if not code:
            print("server disconnected, exiting client")
            sock.close()
            # quit the program
            os._exit(0)
        if code == REGISTER_OK:
            print(f"<< {username} successfully registered, please login")
            username = None
        elif code == REGISTER_USERNAME_EXISTS:
            print(f"<< {username} is already registered, please login")
            username = None
        elif code == LOGIN_OK_NO_UNREAD_MSG:
            print(f"<< welcome {username}, you have no new messages")
        elif code == LOGIN_OK_UNREAD_MSG:
            numMessages = sock.recv(MSG_HEADER_LENGTH)
            numMessages = int.from_bytes(numMessages, "big")
            if numMessages == 1:
                print(f"<< welcome {username}, you have one new message:")
            else:
                print(f"<< welcome {username}, you have {numMessages} new messages:")
            messages = sock.recv(numMessages * (MESSAGE_LENGTH + USERNAME_LENGTH + 2 * DELIMITER_LENGTH)).decode('ascii')
            print(parseMessages(messages), end="")
        elif code == LOGIN_NOT_REGISTERED:
            print(f"<< {username} is not registered. please register before logging in")
            username = None
        elif code == LOGIN_ALREADY_LOGGED_IN:
            print(f"<< {username} is already logged in")
            username = None
        elif code == SEARCH_OK:
            numResults = sock.recv(MSG_HEADER_LENGTH)
            numResults = int.from_bytes(numResults, "big")
            if numResults == 1:
                print("<< 1 username matched your query:")
            else:
                print(f"{numResults} usernames matched your query:")
            results = sock.recv(numResults * (USERNAME_LENGTH + DELIMITER_LENGTH)).decode('ascii')
            print(parseSearchResults(results))
        elif code == SEARCH_NO_RESULTS:
            print("<< no usernames matched your query")
        elif code == SEND_OK_DELIVERED:
            print("<< message delivered")
        elif code == SEND_OK_BUFFERED:
            print(f"<< your message to {recipient} will be delivered when they log in")
        elif code == SEND_RECIPIENT_DNE:
            print(f"<< the user {recipient} does not exist, or has deleted their account")
        elif code == RECEIVE_OK:
            message = sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
            print(parseMessages(message), end="")
        elif code == LOGOUT_OK:
            print("<< successfully logged out")
            username = None
        elif code == DELETE_OK:
            print("<< succesfully logged out and deleted account")
            username = None
        elif code == UNKNOWN_ERROR:
            print("<< unknown error")
        else:
            print("<< unexpected response from server")
            
def serve():
    global username, recipient
    print(">> type a command to begin")
    while True:
        messageBody = None
        command = input("").lower().strip()
        if command not in commandToOpcode:
            print("<< please type an actual command")
            continue
        opcode = commandToOpcode[command]
        if opcode in { OP_REGISTER, OP_LOGIN }:
            if username:
                print(f"<< you are already logged in as {username}, please logout and try again")
                continue
            usernameInput = input(">> please enter username: ").strip()
            if not isValidUsername(usernameInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            messageBody = usernameInput
            username = usernameInput
        elif opcode == OP_SEARCH:
            query = input(">> enter query: ").strip()
            if not isValidQuery(query):
                print("<< search queries must not be blank, must be under 50 characters, and must be comprised of alphanumerics and wildcards (*), please try again")
                continue
            messageBody = query
        elif opcode == OP_SEND:
            if not username:
                print(">> you must be logged in to send a message")
                continue
            recipientInput = input(">> username of recipient: ").strip()
            if not isValidUsername(recipientInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            message = input(">> message: ").strip()
            if not isValidMessage(message):
                print("<< messages must not contain the newline character or the '|' character, must not be blank, and must be under 262 characters, please try again")
                continue
            recipient = recipientInput
            messageBody = formatMessage(username, recipientInput, message)
        elif opcode in { OP_LOGOUT, OP_DELETE } :
            if not username:
                print("<< you are not logged in to an account")
                continue
            usernameInput = input(f">> enter username to confirm {command}: ").strip()
            if not isValidUsername(usernameInput):
                print("<< invalid username")
                continue
            if usernameInput != username:
                print("<< the username typed does not match your username, please try again")
                continue
            messageBody = usernameInput
        else: # only OP_DISCONNECT commands remain: "bye", "disconnect", "quit"
            # logic is already handled in KeyboardInterrupt exception handling
            raise KeyboardInterrupt

        if messageBody:
            # send code and payload
            sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))

def run():
    global username
    try:
        # create a thread to run listen(), which listens for and handles messages 
        # from the server
        listener = threading.Thread(target=listen)
        listener.daemon = True
        listener.start()
        
        # run interpret, which handles user input, parsing, and requests to server, 
        # in the main thread
        serve()
        
    # users may quit via a KeyboardInterrupt, or by typing a command for OP_DISCONNECT
    except KeyboardInterrupt:
        print("\n<< caught interrupt, shutting down connection")
        if username:
            print(f"automatically logging out")
            opcode = OP_LOGOUT
            sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(username, 'ascii'))
            username = None
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    print("starting client...")
    
    host, port = sys.argv[1], int(sys.argv[2])
    serverAddr = (host, port)
    print(f"starting connection to {host}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect_ex(serverAddr)
    run()