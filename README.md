# 262-chat-app
Now distributed-ish!
## Dev Journal: Contains Observations and Discussion!
See [here](https://docs.google.com/document/d/1qOgs7rheuafcUsHj_HPbGeY2kVQCZfjHmDMKqBX9uXE/edit?usp=sharing).
## Installation
Ensure you've got the `socket` and `threading` modules already!

## Running
TODO

The server code must be running on a device before the client code can be run (on the same wifi network). 

To run the server code:
- TODO
- change into the `sockets` directory by typing `cd sockets`
- type `python3 server.py` and click "enter"
- you can specify an optional port to run on as an argument

To run the client code:
- TODO
- change into the `sockets` directory by typing `cd sockets`
- copy the strings next to "host" printed in the terminal of the computer running the server code (ex: `dhcp-10-250-12-215.harvard.edu`) and the "port" (ex: `22067`)
- type `python3 client.py {host} {port}` where `{host}` and `{port}` are the values copied in the previous step

To use the client code:
- try typing any of the commands: register, login, search, send, logout, delete, quit, directly into the command line
- you must be logged in to send, logout, or delete; you must be logged out to register or login
- after typing commands, you will be prompted to enter further details, if applicable; press enter to submit
  - register and login: enter a username that is no more than 50 alphanumeric characters
  - search: enter a query that is no more than 50 alphanumeric characters or wildcards "*", which will match zero or more of any character
  - send: first enter your desired recipient, and then a message that is no more than 262 ASCII characters
  - logout and delete: re-enter your username for confirmation
- incoming messages and results will be printed into the terminal as they come; be warned that this might interrupt your input

To quit the client, either type `quit` into the terminal or press the `Ctrl+C` keys. To quit the server, press the `Ctrl+C` keys. Note that there may be multiple clients running at any given time but only one server.

## Overview of Protocol
TODO

See our journal for details. We stipulate that usernames have max size 50 and messages have max size 262; as we use ASCII encoding, string length is equal to number of bytes used. Messages passed between the server and client will always first contain a 1-byte code determining the operation (for client requests) or status (for server responses). Codes correspond to distinct scenarios and are handled appropriately (see utils.py). Additional information is passed depending on the code, and in most cases consists as strings with ASCII encoding. We use the "|" character (also 1 byte) as a delimiter for message parsing. In particular, the additional information is:
- For login, register, logout, and delete requests, the client passes the username string. For search requests, the client passes the query string.
- For send requests, the client passes a string encoding with the form "sender|recipient|message".
- For login responses, if the user has unread messages, the server sends a 2-byte integer denoting the number of unread messages, and then the encoded messages. Each message has the form "sender|message".
- For search responses, if there are results, the server sends a 2-byte integer denoting the number of results, and then an encoded string of the results joined by "|"s.
- For incoming messages, the server sends the encoded message with the form "sender|message".

Try-excepts are used throughout to handle KeyboardInterrupts and other exceptions. The client and server code will attempt to log out on the event of a program exit. If a client loses connection with the server (e.g. the server shuts down), they will automatically exit.

Our code is thoroughly documented and much of the protocol details are explained within.
