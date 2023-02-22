import unittest
from utils import *
import grpc
from messageservice_pb2 import *
import messageservice_pb2_grpc
import threading


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

if __name__ == '__main__':
    unittest.main()