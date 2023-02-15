import sys
import socket
from utils import *
import threading

username = None
recipient = None
sock = None
query = None

commandToInt = {
    "register" : REGISTER,
    "login" : LOGIN,
    "search" : SEARCH,
    "send" : SEND,
    "logout" : LOGOUT,
    "delete" : DELETE
}

def listen():
    global username
    while True:
        # get the operation code and decode it into a 1 byte integer
        opcode = sock.recv(OPCODE_LENGTH)
        opcode = int.from_bytes(opcode, "big")
        # if the server disconnects, it sends back a None or 0
        if not opcode:
            print("<< detected server disconnect, shutting down")
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            break
        if opcode == REGISTRATION_OK:
            print(f"<< {username} succesfully registered. please login")
            username = None
        elif opcode == USERNAME_EXISTS:
            print(f"<< {username} is already registered. please login")
            username = None
        elif opcode == LOGIN_OK_NO_UNREAD_MSG:
            print(f"<< welcome back {username}")
        elif opcode == LOGIN_OK_UNREAD_MSG:
            numMessages = sock.recv(MSG_HEADER_LENGTH)
            numMessages = int.from_bytes(numMessages, "big")
            print(f"<< you have {numMessages} new messages")
            messages = sock.recv(numMessages * (MESSAGE_LENGTH + USERNAME_LENGTH + 2 * DELIMITER_LENGTH)).decode('ascii')
            print(parseMessages(messages))
        elif opcode == NOT_REGISTERED:
            print(f"<< {username} is not registered. please register before logging in")
            username = None
        elif opcode == ALREADY_LOGGED_IN:
            print(f"<< {username} is already logged in")
        elif opcode == SEARCH_OK:
            numResults = sock.recv(MSG_HEADER_LENGTH)
            numResults = int.from_bytes(numResults, "big")
            print(f"<< {numResults} usernames matched your query:")
            results = sock.recv(numResults * (USERNAME_LENGTH + DELIMITER_LENGTH)).decode('ascii')
            print(parseSearchResults(results))
        elif opcode == NO_RESULTS:
            print("<< no usernames matched your query")
        elif opcode == SENT_INSTANT_OK:
            print(f"<< delivered")
        elif opcode == SENT_CACHED_OK:
            print(f"<< your message to {recipient} will be delivered when they log in")
        elif opcode == RECIPIENT_DNE:
            print(f"<< the user {recipient} does not exist")
        elif opcode == RECEIVED_INSTANT_OK:
            message = sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
            print(parseMessages(message))
        elif opcode == LOGOUT_OK:
            print(f"<< successfully logged out")
            username = None
        elif opcode == DELETE_OK:
            print(f"<< succesfully deleted account")
            username = None
        elif opcode == UNKNOWN_ERROR:
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
            query = input(">>").lower().strip()
            if query not in commandToInt:
                print("<< please type an actual command")
            else:
                queryInt = commandToInt[query]
                if queryInt in { REGISTER, LOGIN }:
                    if username:
                        print(f"<< you are already logged in as {username}, please logout and try again")
                        continue
                    username_ = input(">> please enter username: ").strip()
                    if not isValidUsername(username_):
                        print("<< usernames may not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                        continue
                    messageBody = username_
                    username = username_
                elif queryInt == SEARCH:
                    query = input(">> enter query: ").strip()
                    if not isValidQuery(query):
                        print("<< search queries may not be blank, must be under 50 characters, and must be comprised of alphanumerics and wildcards (*), please try again")
                        continue
                    messageBody = query
                elif queryInt == SEND:
                    if not username:
                        print(">> you must be logged in to send a message")
                        continue
                    recipient_ = input(">> username of recipient: ")
                    if not isValidUsername(recipient_):
                        print("<< invalid username, please try again")
                    message = input(">> message: ").strip()
                    if not isValidMessage(message):
                        print("<< messages must not contain the newline character or the '|' character, may not be blank, and must be under 262 characters, please try again")
                    recipient = recipient_
                    messageBody = formatMessage(username, recipient_, message)
                elif queryInt in { LOGOUT, DELETE } :
                    if not username:
                        print("<< you are not logged in to an account")
                        continue
                    username_ = input(f">> enter username to confirm {query}: ").strip()
                    if not isValidUsername(username_):
                        print("<< invalid username")
                        continue
                    if username_ != username:
                        print("<< the username typed does not match your username, please try again")
                        continue
                    messageBody = username_
                
                if messageBody:
                    # send code and payload
                    sock.sendall(queryInt.to_bytes(OPCODE_LENGTH, "big") + bytes(messageBody, 'ascii'))

    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")

if __name__ == "__main__":    
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    server_addr = (host, port)
    print(f"Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect_ex(server_addr)
    run()