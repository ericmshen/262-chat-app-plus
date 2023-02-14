import sys
import socket
import traceback
from utils import *
import types
import threading

commandToInt = {
    "register" : 0,
    "login" : 1,
    "send" : 2,
    "delete" : 3
}

# query codes


# error codes
SUCCESS = 0
FAILURE = 1
UNKNOWN_ERROR = 2

username = None
sock = None
query = None
    
    # TODO: we should probably have 1) docstrings for each function 2) return values for each functions so we can catch errors

def checkMessages(message : str) -> str:
    messages = message.split("\n")
    retMsg = ""
    for msg in messages:
        messageLst = msg.split("|")
        retMsg += f"{messageLst[0]}: {messageLst[1]}"

    return retMsg
                # TODO: check that they don't use any of our delimiters | or \n (for login)

def sendMessage(recipient : str, messageBody : str) -> int:
    # the connection to the server has not been made yet
    if sock == None:
        print("You must connect to the server before you can send messages")
        return
    # the client is not logged in
    if username == None:
        print("You must login before you can send messages")
        return
    # format the message in the wire format and send
    formattedMessage = formatMessage(username, recipient, messageBody)
    return formattedMessage

def recieveMessages() -> str:
    data = sock.recv(MESSAGE_LENGTH)
    return parseMessage(data)

def listen():
    while True:
        queryCode = sock.recv(1)
        queryCode = int.from_bytes(queryCode, "big")
        errorCode = sock.recv(1)
        errorCode = int.from_bytes(errorCode, "big")
        messageBody = sock.recv(1024).decode('utf-8')

        if not messageBody:
            print("Detected server disconnect, shutting down")
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            break
        
        if errorCode == UNKNOWN_ERROR:
            print("Unknown error...")
            continue

        if queryCode == REGISTER:
            if errorCode == SUCCESS:
                print(f"the username {messageBody} has succesfully been registered")
            elif errorCode == FAILURE:
                print(f"the username {messageBody} is already registered. please login")
        elif queryCode == LOGIN:
            if errorCode == SUCCESS:



        # if code == 
        # response from login
        "register" : 0,
    "login" : 1,
    "send" : 2,
    "delete" : 3
        if code == 0:
            print(messageBody)
        if code == 1:

        print(messageBody.decode('utf-8'))

def run():
    # sock.sendall(b"hello")
    # except KeyboardInterrupt:
    #     print("Caught keyboard interrupt, exiting")
    # finally:
    #     sel.close()
    try:
        # create a thread to listen for and print messages from the server
        listener = threading.Thread(target=listen)
        listener.daemon = True
        listener.start()
        while True:
            query = input()
            if query not in commandToInt:
                print("please type an actual command")
            else:
                queryInt = commandToInt[query]
                if query == "register":
                    messageBody = input("please enter a username to register: ")
                elif query == "login":
                    messageBody = input("please enter your usename to login: ")
                elif query == "send":
                    recipient = input("username of recipient: ")
                    message = input("message: ")
                    sendMessage(recipient, message)
                    messageBody = sendMessage(recipient, message)
                elif query == "delete":
                    messageBody = input("please enter your username to confirm deletion")
                
                # send code
                sock.sendall(queryInt.to_bytes(1, "big"))
                # send payload
                sock.send(bytes(messageBody, 'utf-8'))

    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <host> <port> <socket | gRPC>")
        sys.exit(1)

    # host, port, conn = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    host, port = "127.0.0.1", 22067
    server_addr = (host, port)
    print(f"Starting connection {1} to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.setblocking(False)
    sock.connect_ex(server_addr)

    run()