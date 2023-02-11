import sys
import socket
import selectors
import traceback
import utils
import types


sel = selectors.DefaultSelector()
messages = [b"Message 1 from client.", b"Message 2 from client."]

class Client:
    def __init__(self):
        # self.username = None
        self.username = "charu"
        self.socket = None
    
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
        self.socket.setblocking(False)
        self.socket.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            connid=1,
            msg_total=sum(len(m) for m in messages),
            recv_total=0,
            messages=messages.copy(),
            outb=b"",
        )
        sel.register(self.socket, events, data=data)
    
    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                print(f"Received {recv_data!r} from connection {data.connid}")
                data.recv_total += len(recv_data)
        if mask & selectors.EVENT_WRITE:
            if not data.outb and data.messages:
                data.outb = data.messages.pop(0)
            if data.outb:
                print(f"Sending {data.outb!r} to connection {data.connid}")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]
        
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
    
    def run(self):
        # self.socket.sendall(b"hello")
        # except KeyboardInterrupt:
        #     print("Caught keyboard interrupt, exiting")
        # finally:
        #     sel.close()

        try:
            while True:
                events = sel.select(timeout=1)
                if events:
                    for key, mask in events:
                        self.service_connection(key, mask)
                # Check for a socket being monitored to continue.
                # if not sel.get_map():
                #     break
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            # TODO: also close all sockets
            sel.close()