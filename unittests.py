import unittest
from utils import *
import grpc
import threading
import socket 
import threading
import os

import sys 
sys.path.append('./sockets')
sys.path.append('./grpc_impl')
from sockets.server import service_connection
from grpc_impl.grpc_server import MessageServer, serve
from grpc_impl.grpc_client import *

TEST_SOCKET_SERVER_ADDR = ("localhost", 55566)
TEST_GRPC_SERVER_PORT = "56565"

def startTestSocketServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(TEST_SOCKET_SERVER_ADDR)
    sock.listen(2)
    c, _ = sock.accept()
    service_connection(c)

def startTestgRPCServer():
    serve(TEST_GRPC_SERVER_PORT)

# testing utils
class TestUtils(unittest.TestCase):
    def testFormatMessage(self):
        t1 = formatMessage("sender1", "recipient1", "message1")
        self.assertEqual(t1, "sender1|recipient1|message1")
    
    def testSearchUsernames(self):
        searchStar = searchUsernames(["sender1", "sender2", "sender3"], "*")
        self.assertEqual(searchStar, ["sender1", "sender2", "sender3"])

        searchExists = searchUsernames(["sender1", "sender2", "sender3"], "s*")
        self.assertEqual(searchExists, ["sender1", "sender2", "sender3"])

        searchNotExist = searchUsernames(["sender1", "sender2", "sender3"], "c*")
        self.assertEqual(searchNotExist, [])

        searchExact = searchUsernames(["sender1", "sender2", "sender3"], "sender")
        self.assertEqual(searchExact, [])
    
    def testParseMessages(self):
        parsed = parseMessages("eric|hello!!!\ncharu|bye")
        self.assertEqual(parsed, "eric: hello!!!\ncharu: bye\n")
    
    def testParseSearchResults(self):
        parsed = parseSearchResults("sender1|sender2")
        self.assertEqual(parsed, "sender1\nsender2")
    
    def testIsValidMessage(self):
        messageNotAscii = "☀"
        self.assertFalse(isValidMessage(messageNotAscii))
        
        messageEmpty = ""
        self.assertFalse(isValidMessage(messageEmpty))
        
        messageInvalidCharacters = "|hello\n"
        self.assertFalse(isValidMessage(messageInvalidCharacters))
        
        messageTooLong = "Most known and often used coding is UTF-8. It needs 1 or 4 bytes to represent each symbol. Older coding types takes only 1 byte, so they can't contains. Most known and often used coding is UTF-8. It needs 1 or 4 bytes to represent each symbol. Older coding types takes only 1 byte, so they can't contains. "
        self.assertFalse(isValidMessage(messageTooLong))
        
        messageValid = "this is a valid message"
        self.assertTrue(messageValid)

    def testsIsValidQuery(self):
        queryHasSpace = "hello "
        self.assertFalse(isValidQuery(queryHasSpace))

        queryEmpty = ""
        self.assertFalse(isValidQuery(queryEmpty))

        queryTooLong = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"
        self.assertFalse(isValidQuery(queryTooLong))

        queryValid = "*hi"
        self.assertTrue(isValidQuery(queryValid))
    
    def testIsValidUsername(self):
        usernameHasSpace = "hello "
        self.assertFalse(isValidUsername(usernameHasSpace))

        usernameEmpty = ""
        self.assertFalse(isValidUsername(usernameEmpty))

        usernameTooLong = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"
        self.assertFalse(isValidUsername(usernameTooLong))
        
    def testSocketServer(self):
        testServer = threading.Thread(target=startTestSocketServer)
        testServer.start()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = sock.connect_ex(TEST_SOCKET_SERVER_ADDR)
        self.assertTrue(connected == 0)

    def testgRPCServer(self):
        testServer = threading.Thread(target=startTestgRPCServer)
        testServer.start()
        with grpc.insecure_channel("localhost:" + str(TEST_GRPC_SERVER_PORT)) as channel:
            stub = messageservice_pb2_grpc.MessageServiceStub(channel)
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
        return

if __name__ == '__main__':
    unittest.main()
    os._exit(0)