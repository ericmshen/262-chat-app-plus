import unittest
from utils import *
import threading
from collections import defaultdict
import socket 
import time
import pickle
import os

import sys 
from server import service_connection

SPEEDTEST = False
TEST_SOCKET_SERVER_ADDR = ("localhost", 55566)

serverState = {
    "timestamp": 0,
    "registeredUsers": set(),
    "messageBuffer": defaultdict(list),
}

def startTestSocketServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(TEST_SOCKET_SERVER_ADDR)
    sock.listen(2)
    c, _ = sock.accept()
    service_connection(c)

# testing functionality added in programming project 3
    

    
# testing utils
class TestUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start = time.time()
        
        testServer = threading.Thread(target=startTestSocketServer)
        testServer.daemon = True
        testServer.start()
        cls.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = cls.sock.connect_ex(TEST_SOCKET_SERVER_ADDR)
        assert(connected == 0)
        
        end = time.time()
        print(f"socket init time: {end - start}")
    
    @classmethod
    def tearDownClass(cls):
        # the socket isn't cleaned up, but we ignore this for testing purposes
        cls.sock.close()
        
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
        start = time.time()

        opcode, messageBody = OP_LOGIN, "foo"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_NOT_REGISTERED)
        
        opcode, messageBody = OP_REGISTER, "foo"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == REGISTER_OK)
        
        opcode, messageBody = OP_REGISTER, "foo"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == REGISTER_USERNAME_EXISTS)
        
        opcode, messageBody = OP_LOGIN, "foo"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_OK_NO_UNREAD_MSG)
        
        opcode, messageBody = OP_SEARCH, "f*"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEARCH_OK)
        numResults = self.sock.recv(MSG_HEADER_LENGTH)
        numResults = int.from_bytes(numResults, "big")
        self.assertTrue(numResults == 1)
        results = self.sock.recv(USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
        self.assertTrue(results == "foo")
        
        opcode, messageBody = OP_SEARCH, "noresults"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEARCH_NO_RESULTS)
        
        opcode, messageBody = OP_SEND, "foo|foo|test"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == RECEIVE_OK)
        message = self.sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + DELIMITER_LENGTH).decode('ascii')
        self.assertTrue(message == "foo|test")
        
        opcode, messageBody = OP_SEND, "foo|bar|test"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEND_RECIPIENT_DNE)
        
        opcode, messageBody = OP_LOGOUT, "foo"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGOUT_OK)
        
        opcode = 72
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big"))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == BAD_OPERATION)
        
        opcode, messageBody = OP_REGISTER, "bar"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == REGISTER_OK)
        
        opcode, messageBody = OP_LOGIN, "bar"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_OK_NO_UNREAD_MSG)
        
        opcode, messageBody = OP_SEND, "bar|foo|test2"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEND_OK_BUFFERED)
        
        opcode, messageBody = OP_DELETE, "bar"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == DELETE_OK)
        
        opcode, messageBody = OP_LOGIN, "foo"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == LOGIN_OK_UNREAD_MSG)
        numMessages = self.sock.recv(MSG_HEADER_LENGTH)
        numMessages = int.from_bytes(numMessages, "big")
        self.assertTrue(numMessages == 1)
        messages = self.sock.recv(MESSAGE_LENGTH + USERNAME_LENGTH + 2 * DELIMITER_LENGTH).decode("ascii")
        self.assertTrue(messages == "bar|test2")
        
        opcode, messageBody = OP_SEND, "foo|bar|test3"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        code = self.sock.recv(CODE_LENGTH)
        code = int.from_bytes(code, "big")
        self.assertTrue(code == SEND_RECIPIENT_DNE)
        
        end = time.time()
        print(f"socket op time: {end - start}")
        
        
        if SPEEDTEST:
            start = time.time()
            for i in range(100):
                opcode, messageBody = OP_REGISTER, str(i)
                self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
                code = self.sock.recv(CODE_LENGTH)
                code = int.from_bytes(code, "big")
                if code != REGISTER_OK:
                    self.assertFalse()
        
            end = time.time()
            print(f"socket 100 registers time: {end - start}")
        
        # clean up state
        os.remove("state/server_-1.pickle")
        # give system enough time to delete the file
        time.sleep(0.1)
    
    def testPersistence(self):
        # perform state-changing actions and ensure that they are written to file for the main server
        # register two new users
        opcode, messageBody = OP_REGISTER, "charu"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        time.sleep(0.3)

        opcode, messageBody = OP_REGISTER, "eric"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        time.sleep(0.3)

        # login as charu and send a message to eric (who is not logged in)
        opcode, messageBody = OP_LOGIN, "charu"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        time.sleep(0.3)

        opcode, messageBody = OP_SEND, "charu|eric|hello!"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        
        # give server enough time to write state to file
        time.sleep(0.3)
        with open(f"state/server_-1.pickle", 'rb') as f:
            serverState = pickle.load(f)
        
        self.assertEqual(serverState["registeredUsers"], {"charu", "eric"})
        self.assertEqual(serverState["messageBuffer"]["charu"], [])
        self.assertEqual(serverState["messageBuffer"]["eric"], ["charu|hello!"])

        # clean up state
        os.remove("state/server_-1.pickle")

        # receive all communications from before (cleanup)
        self.sock.recv(2048)
    
    def testPrimaryReplicaCommunication(self):
        testServerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        testServerSock.bind(("localhost", 22072))
        testServerSock.settimeout(1.0)

        opcode, messageBody = OP_REGISTER, "charu2"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        data, _ = testServerSock.recvfrom(1024)
        self.assertEquals(data[0], OP_REGISTER)
        
        opcode, messageBody = OP_REGISTER, "eric2"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        data, _ = testServerSock.recvfrom(1024)
        time.sleep(0.1)

        # login as charu and send a message to eric (who is not logged in)
        opcode, messageBody = OP_LOGIN, "charu2"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        data, _ = testServerSock.recvfrom(1024)
        self.assertEquals(data[0], OP_LOGIN)

        opcode, messageBody = OP_SEND, "charu2|eric2|hello!"
        self.sock.sendall(opcode.to_bytes(CODE_LENGTH, "big") + bytes(messageBody, 'ascii'))
        data, _ = testServerSock.recvfrom(1024)
        self.assertEquals(data[0], OP_SEND)

        # this is NOT a state-changing operation and thus should not be communicated
        opcode, messageBody = OP_SEARCH, "*"

        with self.assertRaises(socket.timeout):
            testServerSock.recvfrom(1024)
        
        # clean up state
        os.remove("state/server_-1.pickle")

        # receive all communications from before (cleanup)
        self.sock.recv(2048)

        # close secondary server
        testServerSock.close()
    

if __name__ == '__main__':
    unittest.main()
    sys.exit(0)