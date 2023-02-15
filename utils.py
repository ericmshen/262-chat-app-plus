from typing import List
import re

MESSAGE_LENGTH = 1024 # TODO: change this

# operation codes
REGISTRATION_OK = 1
USERNAME_EXISTS = 2
LOGIN_OK_NO_UNREAD_MSG = 8
LOGIN_OK_UNREAD_MSG = 9
NOT_REGISTERED = 9
ALREADY_LOGGED_IN = 10
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


def formatMessage(sender : str, recipient: str, messageBody: str):
    return f"{sender}|{recipient}|{messageBody}"

# wildcard search interprets * as zero or more of ANY character
def searchUsernames(usernames : List[str], query : str):
    if len(usernames) == 0: return []
    if len(query) == 0:
        return usernames
    q = query.replace("*", ".*")
    return list(filter(lambda x: re.match(q, x), usernames))

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