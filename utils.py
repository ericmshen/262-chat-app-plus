from typing import List
import re
import string

# operation codes
REGISTRATION_OK = 1
USERNAME_EXISTS = 2
LOGIN_OK_NO_UNREAD_MSG = 8
LOGIN_OK_UNREAD_MSG = 9
NOT_REGISTERED = 10
ALREADY_LOGGED_IN = 11
SEARCH_OK = 16
NO_RESULTS = 17
SENT_INSTANT_OK = 24
SENT_CACHED_OK = 25
RECIPIENT_DNE = 26
RECEIVED_INSTANT_OK = 32
LOGOUT_OK = 40
DELETE_OK = 48
UNKNOWN_ERROR = 127

# command codes
REGISTER = 1
LOGIN = 2
SEARCH = 3
SEND = 4
LOGOUT = 5
DELETE = 6

# consts
MESSAGE_LENGTH = 262
USERNAME_LENGTH = 50
DELIMITER_LENGTH = 1
OPCODE_LENGTH = 1
MSG_HEADER_LENGTH = 2


def formatMessage(sender : str, recipient: str, messageBody: str):
    return f"{sender}|{recipient}|{messageBody}"

def parseMessages(message : str) -> str:
    messages = message.split("\n")
    retMsg = ""
    for msg in messages:
        messageLst = msg.split("|")
        retMsg += f"{messageLst[0]}: {messageLst[1]} \n"

    return retMsg

def parseSearchResults(result : str) -> str:
    results = result.split("|")
    return "\n".join(results)

# wildcard search interprets * as zero or more of ANY character
def searchUsernames(usernames : List[str], query : str):
    if len(usernames) == 0: return []
    if len(query) == 0:
        return usernames
    q = query.replace("*", ".*")
    return list(filter(lambda x: re.match(q, x), usernames))

def isValidUsername(username : str):
    return username and username.isalnum() and len(username) <= 50 

def isValidQuery(query : str):
    return ( 
        query and 
        set(query).issubset(set(string.ascii_lowercase + string.digits + '*')) and 
        len(query) <= 50 
    )

def isValidMessage(message : str):
    return (
        message and
        "\n" not in message and "|" not in message and
        len(message) <= 262
    )

# TODO: move tests elsewhere
if __name__ == "__main__":
    print(formatMessage("sender1", "recipient1", "message1"))
    print(formatMessage("sender1", "recipient1", "message2"))
    print(formatMessage("sender1", "recipient1", "message3"))
    print(searchUsernames(["sender1", "sender2", "sender3"], "*"))
    print(searchUsernames(["sender1", "sender2", "sender3"], "s*"))
    print(searchUsernames(["sender1", "sender2", "sender3"], "c*"))
    print(searchUsernames(["sender1", "sender2", "sender3"], "*1"))
    print(searchUsernames(["sender1", "sender2", "sender3"], "sender"))