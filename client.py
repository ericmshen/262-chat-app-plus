import sys
import socket
from utils import *
import threading
import os
from _thread import interrupt_main

# Username of the logged in user on the client code. If None, no user is logged in.
# We use this as a proxy for detecting if the client code has someone logged in or not.
username = None

# Empty variable for specifying recipient.
recipient = None

# Connected socket.
sock = None

# Command read from input.
command = None

def listen():
    global username
    while True:
        # get the operation code and decode it into a 1 byte integer
        try:
            code = sock.recv(CODE_LENGTH)
            code = int.from_bytes(code, "big")
        except:
            print("unable to connect to server, shutting down")
            sock.close()
            # quit the program
            os._exit(0)
        # if the server disconnects, it sends back a None or 0
        if not code:
            print("detected server disconnect, shutting down")
            sock.close()
            # quit the program
            os._exit(0)
        if code == REGISTRATION_OK:
            print(f"<< {username} succesfully registered. please login")
            username = None
        elif code == USERNAME_EXISTS:
            print(f"<< {username} is already registered. please login")
            username = None
        elif code == LOGIN_OK_NO_UNREAD_MSG:
            print(f"<< welcome back {username}")
        elif code == LOGIN_OK_UNREAD_MSG:
            numMessages = sock.recv(MSG_HEADER_LENGTH)
            numMessages = int.from_bytes(numMessages, "big")
            print(f"<< you have {numMessages} new messages")
            messages = sock.recv(numMessages * (MESSAGE_LENGTH + USERNAME_LENGTH + 2 * DELIMITER_LENGTH)).decode('ascii')
            print(parseMessages(messages))
        elif code == NOT_REGISTERED:
            print(f"<< {username} is not registered. please register before logging in")
            username = None
        elif code == ALREADY_LOGGED_IN:
            print(f"<< {username} is already logged in")
            username = None
        elif code == SEARCH_OK:
            numResults = sock.recv(MSG_HEADER_LENGTH)
            numResults = int.from_bytes(numResults, "big")
            print(f"<< {numResults} usernames matched your query:")
            results = sock.recv(numResults * (USERNAME_LENGTH + DELIMITER_LENGTH)).decode('ascii')
            print(parseSearchResults(results))
        elif code == NO_RESULTS:
            print("<< no usernames matched your query")
        elif code == SENT_INSTANT_OK:
            print(f"<< delivered")
        elif code == SENT_CACHED_OK:
            print(f"<< your message to {recipient} will be delivered when they log in")
        elif code == RECIPIENT_DNE:
            print(f"<< the user {recipient} does not exist")
        elif code == RECEIVED_INSTANT_OK:
            message = sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
            print(parseMessages(message))
        elif code == LOGOUT_OK:
            print(f"<< successfully logged out")
            username = None
        elif code == DELETE_OK:
            print(f"<< succesfully deleted account")
            username = None
        elif code == UNKNOWN_ERROR:
            print(f"<< unknown error")

def run():
    global username, recipient
    try:
        # create a thread to listen for and print messages from the server
        listener = threading.Thread(target=listen)
        listener.daemon = True
        listener.start()
        while True:
            messageBody = None
            command = input("").lower().strip()
            if command not in commandToInt:
                print("<< please type an actual command")
                continue
            opcode = commandToInt[command]
            if opcode in { REGISTER, LOGIN }:
                if username:
                    print(f"<< you are already logged in as {username}, please logout and try again")
                    continue
                usernameInput = input(">> please enter username: ").strip()
                if not isValidUsername(usernameInput):
                    print("<< usernames may not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                    continue
                messageBody = usernameInput
                username = usernameInput
            elif opcode == SEARCH:
                query = input(">> enter query: ").strip()
                if not isValidQuery(query):
                    print("<< search queries may not be blank, must be under 50 characters, and must be comprised of alphanumerics and wildcards (*), please try again")
                    continue
                messageBody = query
            elif opcode == SEND:
                if not username:
                    print(">> you must be logged in to send a message")
                    continue
                recipientInput = input(">> username of recipient: ")
                if not isValidUsername(recipientInput):
                    print("<< invalid username, please try again")
                message = input(">> message: ").strip()
                if not isValidMessage(message):
                    print("<< messages must not contain the newline character or the '|' character, may not be blank, and must be under 262 characters, please try again")
                recipient = recipientInput
                messageBody = formatMessage(username, recipientInput, message)
            elif opcode in { LOGOUT, DELETE } :
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
            
            if messageBody:
                # send code and payload
                sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))

    except KeyboardInterrupt:
        print("\nCaught interrupt, exiting")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    serverAddr = (host, port)
    print(f"Starting connection to {serverAddr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect_ex(serverAddr)
    run()