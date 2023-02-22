import sys
import socket
from utils import *
import threading
import os

# The client is at a high level composed of two threads which handle sending and receiving
# respectively over a socket. After establishing a connection, listen() monitors the socket
# for incoming data from the server and handles it according to the wire protocol. serve()
# reads user input, applies client-side checks to operations if applicable, and sends data
# to the server according to the wire protocol. 

# *** VARIABLES *** (to track state of client in an easy, class-free manner)
# username of the logged in user on the client side: if None, no user is logged in
# we use this as a proxy for detecting if the client code has someone logged in or not
username = None

# empty variable for specifying recipient
recipient = None

# connected socket accessed by all threads
sock = None

def listen():
    """ Services all receiving functionality over the client socket. Over the lifetime of 
    the connection, it loops and reads from the socket. It first reads a 1-byte status 
    code as specified by the wire protocol, followed by status-specific data. It processes
    the output and displays the results to the user in the terminal. """
    
    global username
    
    # helper function to exit the client
    def stop():
        print("not connected to server, exiting client")
        # close the connection
        sock.close()
        # use os._exit to quickly kill everything from the thread running listen()
        os._exit(0)
    
    # loop until socket closed or program interrupted; the overall message from the server
    # is a status code followed by status-specific data
    while True:
        # get the status code and decode it into a 1 byte integer
        try:
            code = sock.recv(CODE_LENGTH)
            code = int.from_bytes(code, "big")
        # if try fails, there's an error communicating with the server; exit
        except: stop()
        # if the server disconnects, it sends back a None or 0; also exit
        if not code:
            print("server disconnected, exiting client")
            sock.close()
            os._exit(0)

        # all status codes map a unique server response to a particular operation
        # all receives are try-excepted; in the case of ANY error, we exit
        
        # *** REGISTER ***
        # don't "login" (set the username) yet; the user should explicitly login
        if code == REGISTER_OK:
            print(f"<< {username} successfully registered, please login")
            username = None
        elif code == REGISTER_USERNAME_EXISTS:
            print(f"<< {username} is already registered, please login")
            username = None
        
        # *** LOGIN ***
        elif code == LOGIN_OK_NO_UNREAD_MSG:
            print(f"<< welcome {username}, you have no new messages")
        # with unread messages, receive the number of messages and then the messages themselves
        elif code == LOGIN_OK_UNREAD_MSG:
            # we first read the number of messages from the header
            try:
                numMessages = sock.recv(MSG_HEADER_LENGTH)
                numMessages = int.from_bytes(numMessages, "big")
                # receive the buffered messages; each message has the form <sender>|<message>\n, so 
                # assuming newlines are encoded in DELIMITER_LENGTH bytes, the overall size of the 
                # response is at most MESSAGE_LENGTH + USERNAME_LENGTH + 2 * DELIMITER_LENGTH
                messages = sock.recv(numMessages * (MESSAGE_LENGTH + USERNAME_LENGTH + 2 * DELIMITER_LENGTH)).decode('ascii')
            except: stop()
            # print the buffered messages
            if numMessages == 1:
                print(f"<< welcome {username}, you have one new message:")
            else:
                print(f"<< welcome {username}, you have {numMessages} new messages:")
            print(parseMessages(messages), end="")
        # if there's an error, clear the global username variable; login did not succeed
        elif code == LOGIN_NOT_REGISTERED:
            print(f"<< {username} is not registered. please register before logging in")
            username = None
        elif code == LOGIN_ALREADY_LOGGED_IN:
            print(f"<< {username} is already logged in")
            username = None
            
        # *** SEARCH ***
        elif code == SEARCH_OK:
            # read the number of results from the header
            try:
                numResults = sock.recv(MSG_HEADER_LENGTH)
                numResults = int.from_bytes(numResults, "big")
                # receive the number of results themselves; each result has the form <username>|, so
                # the overall size of the response is at most USERNAME_LENGTH + DELIMITER_LENGTH
                results = sock.recv(numResults * (USERNAME_LENGTH + DELIMITER_LENGTH)).decode('ascii')
            except: stop()
            # print the results
            if numResults == 1:
                print("<< 1 username matched your query:")
            else:
                print(f"{numResults} usernames matched your query:")
            print(parseSearchResults(results))
        elif code == SEARCH_NO_RESULTS:
            print("<< no usernames matched your query")
        
        # *** SEND ***
        elif code == SEND_OK_DELIVERED:
            print(f"<< message delivered to {recipient}")
        elif code == SEND_OK_BUFFERED:
            print(f"<< your message to {recipient} will be delivered when they log in")
        elif code == SEND_RECIPIENT_DNE:
            print(f"<< the user {recipient} does not exist, or has deleted their account")
        elif code == SEND_FAILED:
            print(f"<< your message to {recipient} could not be delivered, please try again later")
            
        # *** RECEIVE ***
        # this status code corresponds to a client RECEIVING an incoming messsage, which will be
        # formatted as <sender>|<message>
        elif code == RECEIVE_OK:
            try:
                message = sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
            except: stop()
            if username == recipient:
                print("<< congratulations, you sent a message to yourself")
            print(parseMessages(message), end="")
        
        # *** LOGOUT ***
        elif code == LOGOUT_OK:
            print("<< successfully logged out")
            username = None
        
        # *** DELETE ***
        elif code == DELETE_OK:
            print("<< succesfully logged out and deleted account")
            username = None
        
        # something went wrong in the server
        elif code == UNKNOWN_ERROR:
            print("<< unknown error")
        else:
            print("<< unexpected response from server")
            
def serve():
    """ Services all sending functionality over the client socket. Over the lifetime of 
    the connection, it loops and reads from the input (in the terminal). It reads an 
    operation, followed by operation-specific data. It processes the client input, applies
    client-side checks if applicable, and sends data over the socket. """
    global username, recipient
    print(">> type a command to begin: {register, login, search, send, logout, delete, quit}")
    
    # loop while reading user input: the overall message to send to the server will comprise of
    # the operation code, then operation-specific data
    while True:
        # the first input is the desired operation
        messageBody = None
        command = input("").lower().strip()
        if command not in commandToOpcode:
            print("<< please type an actual command")
            continue
        # find the operation code and handle based on that
        opcode = commandToOpcode[command]
        
        # *** REGISTER AND LOGIN ***
        if opcode in { OP_REGISTER, OP_LOGIN }:
            # can't do either operation if you're already logged in
            if username:
                print(f"<< you are already logged in as {username}, please logout and try again")
                continue
            # in both operations, just prompt the user for their username
            usernameInput = input(">> please enter username: ").strip()
            # client side check for valid username
            if not isValidUsername(usernameInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            # also send the username to the server
            messageBody = usernameInput
            
            # tentatively set username to be the input, marking the user as logged in on the 
            # client side; if there's an error, the listen() function will handle it and set the
            # username back to None
            username = usernameInput
        
        # *** SEARCH ***
        elif opcode == OP_SEARCH:
            # prompt the user for the search query, client-side check for validity
            query = input(">> enter query: ").strip()
            if not isValidQuery(query):
                print("<< search queries must not be blank, must be under 50 characters, and must be comprised of alphanumerics and wildcards (*), please try again")
                continue
            # send the query to the server
            messageBody = query
            
        # *** SEND ***
        elif opcode == OP_SEND:
            # can't send if you're not logged in
            if not username:
                print(">> you must be logged in to send a message")
                continue
            # read the receiver username and then the message; client-side checks for validity
            recipientInput = input(">> username of recipient: ").strip()
            if not isValidUsername(recipientInput):
                print("<< usernames must not be blank, must be under 50 characters, and must be alphanumeric, please try again")
                continue
            message = input(">> message: ").strip()
            if not isValidMessage(message):
                print(f"<< messages must contain only ASCII (English) characters, not contain newlines or '|', must not be blank, and must be under 262 characters (current length {len(message)} characters), please try again")
                continue
            # store the recipient globally so we can reference it in listen()
            recipient = recipientInput
            # send the sender, recipient, and message to the server
            messageBody = formatMessage(username, recipientInput, message)
        
        # *** LOGOUT AND DELETE ***
        elif opcode in { OP_LOGOUT, OP_DELETE } :
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
            # send the username to the server
            messageBody = usernameInput
        
        # only OP_DISCONNECT commands remain: "bye", "disconnect", "quit"
        # logic is already handled in KeyboardInterrupt exception handling
        else: 
            raise KeyboardInterrupt

        # if messageBody was set then the operation is valid to send
        if messageBody:
            # send code and payload
            sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))

def run():
    """ Function to initialize the listen and serve operations upon program start. """
    global username
    try:
        # create a separate thread to run listen()
        listener = threading.Thread(target=listen)
        listener.daemon = True
        listener.start()
        
        # run interpret, which handles user input, parsing, and requests to server, 
        # in the main thread
        serve()
        
    # users may quit via a KeyboardInterrupt, or by typing a command for OP_DISCONNECT
    except:
        print("\n<< caught interrupt, shutting down connection")
        # if the user is still logged in, send a logout message before closing the connection
        if username:
            print(f"automatically logging out")
            opcode = OP_LOGOUT
            sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(username, 'ascii'))
            username = None
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        sys.exit(0)

if __name__ == "__main__":
    # must specify a host and port to connect to
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    print("starting client...")
    
    # try to initialize the socket; connect_ex returns a code instead of exception
    host, port = sys.argv[1], int(sys.argv[2])
    serverAddr = (host, port)
    print(f"starting connection to {host}:{port}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connected = sock.connect_ex(serverAddr)
    if connected != 0:
        print("<< failed to create socket connection to server, exiting client")
        sys.exit(1)
    run()