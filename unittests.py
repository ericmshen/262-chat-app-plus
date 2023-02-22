import unittest
from utils import *
import grpc
import threading
import socket 
import threading

import sys 
sys.path.append('./sockets')
sys.path.append('./grpc_impl')
from sockets.server import service_connection
from grpc_impl.grpc_server import serve
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
        parsed = parseMessages("a|hello!!!")
        self.assertEqual(parsed, "a: hello!!!\n")
        
        parsed = parseMessages("a|hello!!!\nb|bye")
        self.assertEqual(parsed, "a: hello!!!\nb: bye\n")
    
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
        testServer.daemon = True
        testServer.start()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = sock.connect_ex(TEST_SOCKET_SERVER_ADDR)
        self.assertTrue(connected == 0)
        
        opcode, messageBody = OP_LOGIN, "foo"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_NOT_REGISTERED)
        
        opcode, messageBody = OP_REGISTER, "foo"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == REGISTER_OK)
        
        opcode, messageBody = OP_REGISTER, "foo"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == REGISTER_USERNAME_EXISTS)
        
        opcode, messageBody = OP_LOGIN, "foo"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_OK_NO_UNREAD_MSG)
        
        opcode, messageBody = OP_SEARCH, "*"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEARCH_OK)
        numResults = sock.recv(MSG_HEADER_LENGTH)
        numResults = int.from_bytes(numResults, "big")
        self.assertTrue(numResults == 1)
        results = sock.recv(USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
        self.assertTrue(results == "foo")
        
        opcode, messageBody = OP_SEARCH, "noresults"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEARCH_NO_RESULTS)
        
        opcode, messageBody = OP_SEND, "foo|foo|test"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == RECEIVE_OK)
        message = sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
        self.assertTrue(message == "foo|test")
        
        opcode, messageBody = OP_SEND, "foo|bar|test"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEND_RECIPIENT_DNE)
        
        opcode, messageBody = OP_LOGOUT, "foo"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGOUT_OK)
        
        opcode = 72
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big"))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == BAD_OPERATION)
        
        opcode, messageBody = OP_REGISTER, "bar"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == REGISTER_OK)
        
        opcode, messageBody = OP_LOGIN, "bar"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_OK_NO_UNREAD_MSG)
        
        opcode, messageBody = OP_SEND, "bar|foo|test2"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEND_OK_BUFFERED)
        
        opcode, messageBody = OP_DELETE, "bar"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == DELETE_OK)
        
        opcode, messageBody = OP_LOGIN, "foo"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_OK_UNREAD_MSG)
        numMessages = sock.recv(MSG_HEADER_LENGTH)
        numMessages = int.from_bytes(numMessages, "big")
        self.assertTrue(numMessages == 1)
        messages = sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + 2 * DELIMITER_LENGTH).decode("ascii")
        self.assertTrue(messages == "bar|test2")
        
        opcode, messageBody = OP_SEND, "foo|bar|test3"
        sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEND_RECIPIENT_DNE)
        
        # the socket isn't cleaned up, but we ignore this for testing purposes
        sock.close()

    def testgRPCServer(self):
        testServer = threading.Thread(target=startTestgRPCServer)
        testServer.daemon = True
        testServer.start()
        with grpc.insecure_channel("localhost:" + str(TEST_GRPC_SERVER_PORT)) as channel:
            stub = messageservice_pb2_grpc.MessageServiceStub(channel)
            self.assertTrue(stub != None)
            
            response = stub.Login(UsernameRequest(username="foo"))
            self.assertTrue(response.statusCode == LOGIN_NOT_REGISTERED)
            
            response = stub.Register(UsernameRequest(username="foo"))
            self.assertTrue(response.statusCode == REGISTER_OK)
            
            response = stub.Register(UsernameRequest(username="foo"))
            self.assertTrue(response.statusCode == REGISTER_USERNAME_EXISTS)
            
            response = stub.Login(UsernameRequest(username="foo"))
            self.assertTrue(response.statusCode == LOGIN_OK_NO_UNREAD_MSG)
            
            response = stub.Search(SearchRequest(query="*"))
            self.assertTrue(response.statusCode == SEARCH_OK)
            self.assertTrue(len(response.results) == 1)
            self.assertTrue(response.results[0] == "foo")
            
            response = stub.Search(SearchRequest(query="noresults"))
            self.assertTrue(response.statusCode == SEARCH_NO_RESULTS)
            
            response = stub.Send(MessageRequest(sender="foo", recipient="foo", body="test"))
            self.assertTrue(response.statusCode == SEND_OK_DELIVERED)
            
            response = stub.Send(MessageRequest(sender="foo", recipient="bar", body="no"))
            self.assertTrue(response.statusCode == SEND_RECIPIENT_DNE)
            
            response = stub.Logout(UsernameRequest(username="foo"))
            self.assertTrue(response.statusCode == LOGOUT_OK)
            
            response = stub.Register(UsernameRequest(username="bar"))
            self.assertTrue(response.statusCode == REGISTER_OK)
            
            response = stub.Login(UsernameRequest(username="bar"))
            self.assertTrue(response.statusCode == LOGIN_OK_NO_UNREAD_MSG)
            
            response = stub.Send(MessageRequest(sender="bar", recipient="foo", body="test2"))
            self.assertTrue(response.statusCode == SEND_OK_BUFFERED)
            
            response = stub.Delete(UsernameRequest(username="bar"))
            self.assertTrue(response.statusCode == DELETE_OK)
            
            response = stub.Login(UsernameRequest(username="foo"))
            self.assertTrue(response.statusCode == LOGIN_OK_UNREAD_MSG)
            self.assertTrue(len(response.messages) == 1)
            self.assertTrue(response.messages[0].sender == "bar")
            self.assertTrue(response.messages[0].body == "test2")
            
            response = stub.Send(MessageRequest(sender="foo", recipient="bar", body="test3"))
            self.assertTrue(response.statusCode == SEND_RECIPIENT_DNE)

if __name__ == '__main__':
    unittest.main()
    sys.exit(0)