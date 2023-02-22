from typing import List
import re
import string

# *** CONSTS ***
# operation codes
OP_REGISTER = 1
OP_LOGIN = 2
OP_SEARCH = 3
OP_SEND = 4
OP_LOGOUT = 5
OP_DELETE = 6
OP_DISCONNECT = 7

# server status codes
REGISTER_OK = 1
REGISTER_USERNAME_EXISTS = 2
LOGIN_OK_NO_UNREAD_MSG = 8
LOGIN_OK_UNREAD_MSG = 9
LOGIN_NOT_REGISTERED = 10
LOGIN_ALREADY_LOGGED_IN = 11
SEARCH_OK = 16
SEARCH_NO_RESULTS = 17
SEND_OK_DELIVERED = 24
SEND_OK_BUFFERED = 25
SEND_RECIPIENT_DNE = 26
SEND_FAILED = 27
RECEIVE_OK = 32
LOGOUT_OK = 40
DELETE_OK = 48
BAD_OPERATION = 126
UNKNOWN_ERROR = 127

# map strings to operation codes for parsing of user input
commandToOpcode = {
    "register" : OP_REGISTER,
    "login" : OP_LOGIN,
    "search" : OP_SEARCH,
    "send" : OP_SEND,
    "logout" : OP_LOGOUT,
    "delete" : OP_DELETE,
    "quit" : OP_DISCONNECT,
    "bye" : OP_DISCONNECT,
    "disconnect" : OP_DISCONNECT,
}

# constants used in sending messages
MESSAGE_LENGTH = 262
USERNAME_LENGTH = 50
DELIMITER_LENGTH = 1
CODE_LENGTH = 1
MSG_HEADER_LENGTH = 2

# *** HELPER FUNCTIONS ***
# take a sender, recipient, and message body and return a string that represents
# the encoding of the message sent over the socket
def formatMessage(sender : str, recipient: str, body: str):
    return f"{sender}|{recipient}|{body}"

# complementary to the above: parses a string of incoming messages into a form 
# that can be printed in the terminal, with messages separated by newlines
def parseMessages(input : str) -> str:
    messages = input.split("\n")
    retMsg = ""
    for msg in messages:
        # <receiver>|<message> => <receiver>: <message>
        messageLst = msg.split("|")
        retMsg += f"{messageLst[0]}: {messageLst[1]}\n"
    return retMsg

# ibid for search results: expands separators (|s) into newlines
def parseSearchResults(result : str) -> str:
    results = result.split("|")
    return "\n".join(results)

# given a list of total usernames and a query, returns the usernames matching
# the query; note: wildcard search interprets * as ZERO or more of ANY character
def searchUsernames(usernames : List[str], query : str):
    if len(usernames) == 0: return []
    if len(query) == 0:
        return usernames
    q = "^" + query + "$"
    q = q.replace("*", ".*")
    return list(filter(lambda x: re.match(q, x), usernames))

# check if a username is valid: it must not be blank, be alphanumeric, and be
# no more than 50 characters
def isValidUsername(username : str):
    return username and username.isalnum() and len(username) <= USERNAME_LENGTH 

# similar to isValidUsername, but for queries (can also handle *)
def isValidQuery(query : str):
    return ( 
        query and 
        set(query).issubset(set(string.ascii_lowercase + string.ascii_uppercase + string.digits + '*')) and 
        len(query) <= USERNAME_LENGTH 
    )

# messages must contain only ASCII (English) characters, not contain newlines 
# or separators (|s), and be no more than 262 characters
def isValidMessage(message : str):
    # simple way to check if message is ASCII: try encoding it
    try:
        message.encode("ascii")
        return (
            message and
            "\n" not in message and "|" not in message and
            len(message) <= MESSAGE_LENGTH
        )
    except UnicodeEncodeError:
        return False
