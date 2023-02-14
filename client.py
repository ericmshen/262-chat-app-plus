import sys
import socket
import selectors
import traceback
import utils
import types
import threading


sel = selectors.DefaultSelector()

class Client:
    def __init__(self):
        # self.username = None
        self.username = "charu"
        self.socket = None
        self.query = None
    
    # TODO: we should probably have 1) docstrings for each function 2) return values for each functions so we can catch errors
    # def start_connection(self, host : str, port : str):
    #     '''
    #     write docstring here
    #     '''
    #     address = (host, port)
    #     print(f"Connecting to server at {address}")
    #     self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.socket.connect(address)
    #     # events = selectors.EVENT_READ | selectors.EVENT_WRITE
    #     # sel.register(self.socket, events, data=b"hello")

    def start_connections(self, host, port, num_conns):
        server_addr = (host, port)
        print(f"Starting connection {1} to {server_addr}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.socket.setblocking(False)
        self.socket.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        # data = types.SimpleNamespace(
        #     connid=1,
        #     msg_total=sum(len(m) for m in messages),
        #     recv_total=0,
        #     messages=[],
        #     outb=b"",
        # )
        sel.register(self.socket, events, data=None)
        # print(sel)
    
    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            print("HERE")
            recv_data = sock.recv(1024)  # Should be ready to read
            print(f"Received {recv_data!r}")
            # if recv_data:
            #     print(f"Received {recv_data!r} from connection {data.connid}")
            #     data.recv_total += len(recv_data)
        if mask & selectors.EVENT_WRITE and data:
            sent = sock.send(data)  # Should be ready to write
            self.query = None
    
    def checkMessages(self, message : str) -> str:
        messages = message.split("\n")
        retMsg = ""
        for msg in messages:
            messageLst = msg.split("|")
            retMsg += f"{messageLst[0]}: {messageLst[1]}"

        return retMsg
                    # TODO: check that they don't use any of our delimiters | or \n (for login)

    def sendMessage(self, recipient : str, messageBody : str) -> int:
        # the connection to the server has not been made yet
        if self.socket == None:
            print("You must connect to the server before you can send messages")
            return
        # the client is not logged in
        if self.username == None:
            print("You must login before you can send messages")
            return
        # format the message in the wire format and send
        formattedMessage = utils.formatMessage(self.username, recipient, messageBody)
        self.socket.sendall(bytes(formattedMessage, 'utf-8'))
    
    def recieveMessages(self) -> str:
        data = self.socket.recv(utils.MESSAGE_LENGTH)
        return utils.parseMessage(data)
    
    def listen(self):
        print(self.socket.recv(1024))
    
    def run(self):
        # self.socket.sendall(b"hello")
        # except KeyboardInterrupt:
        #     print("Caught keyboard interrupt, exiting")
        # finally:
        #     sel.close()
        try:
            threading1 = threading.Thread(target=self.listen)
            threading1.daemon = True
            threading1.start()
            while True:
                self.query = input(">> ")
                if self.query == "register":
                    username = input('please enter a username: ')
                    self.socket.sendall(bytes(username, 'utf-8'))
                elif self.query == "send":
                    self.socket.sendall(b"send")
                    recipient = input("username of recipient: ")
                    message = input("message: ")
                    self.sendMessage(recipient, message)
                # elif self.query == "check":
                #     messageBuf = ""
                #     message = ""
                #     self.socket.send(b"check")
                #     messageBuf = self.socket.recv(1024).decode("utf-8") 
                    # while True:
                    #     message = self.socket.recv(1024)
                    #     if not message:
                    #         break

                    #     messageBuf += str(message)
                
                    # print(self.checkMessages(messageBuf))
                else :
                    print("please type an actual command")

                # events = sel.select(timeout=1)
                # if events:
                #     for key, mask in events:
                #         self.service_connection(key, mask)
                # Check for a socket being monitored to continue.
                # if not sel.get_map():
                #     break
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            # TODO: also close all sockets
            sel.close()