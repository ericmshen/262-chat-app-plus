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

global username
global usrTemp

username = None
usrTemp = None
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

def listen():
    global username, usrTemp
    while True:
        errorCode = sock.recv(1)
        errorCode = int.from_bytes(errorCode, "big")

        if not errorCode:
            print("detected server disconnect, shutting down")
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            break
        
        if errorCode == REGISTRATION_OK:
            print(f"succesfully registered")
        elif errorCode == USERNAME_EXISTS:
            print(f"username is already registered. please login")
        elif errorCode == LOGIN_OK_NO_UNREAD_MSG:
            print(f"welcome back")
            username = usrTemp
        elif errorCode == LOGIN_OK_UNREAD_MSG:
            numMessages = sock.recv(1)
            numMessages = int.from_bytes(numMessages, "big")
            username = usrTemp
            print(f"you have {numMessages} new messages")
            # TODO: change to the actual # bytes we are reading
            messages = sock.recv(numMessages * 500)
            # TODO: parse the message that is sent
            print(messages)
        elif errorCode == NOT_REGISTERED:
            print(f"the requested user is not registered. please register before logging in")
        elif errorCode == ALREADY_LOGGED_IN:
            print(f"the requested user is already logged in another terminal window")
        elif errorCode == SEARCH_OK:
            pass
        elif errorCode == NO_RESULTS:
            pass
        elif errorCode == SENT_INSTANT_OK:
            print(f"delivered")
        elif errorCode == SENT_CACHED_OK:
            print(f"your message will be delivered when the recipient logs in")
        elif errorCode == RECIPIENT_DNE:
            print(f"the recipient does not exist")
        elif errorCode == RECEIVED_INSTANT_OK:
            # TODO: change the 500 here
            message = sock.recv(500)
            print(message)
        elif errorCode == LOGOUT_OK:
            print(f"successfully logged out")
            username = None
            usrTemp = None
        elif errorCode == DELETE_OK:
            print(f"succesfully deleted account")
            username = None
            usrTemp = None
        elif errorCode == UNKNOWN_ERROR:
            print(f"unknown error")

def run():
    global usrTemp
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
            messageBody = None
            query = input()
            if query not in commandToInt:
                print("please type an actual command")
            else:
                queryInt = commandToInt[query]
                if query == "register":
                    messageBody = input("please enter a username to register: ")
                elif query == "login":
                    messageBody = input("please enter your username to login: ")
                    usrTemp = messageBody
                    # do some checks
                elif query == "send":
                    recipient = input("username of recipient: ")
                    message = input("message: ")
                    sendMessage(recipient, message)
                    messageBody = sendMessage(recipient, message)
                elif query == "delete":
                    messageBody = input("please enter your username to confirm deletion")
                
                if messageBody:
                    # send code
                    sock.sendall(queryInt.to_bytes(1, "big"))
                    # send payload
                    sock.send(bytes(messageBody, 'utf-8'))

    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    server_addr = (host, port)
    print(f"Starting connection {1} to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect_ex(server_addr)

    run()