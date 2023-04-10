# 262-chat-app-plus
An extension of our socket chat app from Design Project 1. Now distributed-ish!
## Dev Journal: Contains Details and Discussion!
See [here](https://docs.google.com/document/d/1qOgs7rheuafcUsHj_HPbGeY2kVQCZfjHmDMKqBX9uXE/edit?usp=sharing).
## Installation
We use Python. Ensure you've got the `socket` and `threading` modules already!

## Running
Three server instantiations should be run from the terminal, possibly from different devices. In order to achieve persistence, they should be initialized within five seconds of each other. On each device where the server code is being run, all of the server computers' host names should already be known. This can be done by running `getaddr.py` on each device prior to running the code. 

All server code must be running on a device before the client code can be run. All server and client code should be running on the same wifi network.

To run the server code:
- open three total terminals
- in each terminal, type `python3 server.py <ID> <HOST 0> <HOST 1> <HOST 2>` where the ID is the server ID to be run in that terminal (either 0, 1, or 2), and the HOSTs are the host names of the respective computer running the server code in that terminal (to run everything locally each HOST can be `localhost`)
- make sure each terminal runs a separate server ID, and that the host names correspond to the hosts of the computers running each corresponding server (order matters); for example, if host 1 is running on `host.harvard.edu`, then `<HOST 1>` should be `host.harvard.edu`
- run each command to boot up the servers within 5 seconds of each other
- you are ready to run client code once each server has printed that they are listening for clients
- try shutting down servers unexpectedly by ^Cing

To run the client code:
- get the three hostnames of the server instances as above
- in a terminal, type `python3 client.py <HOST 0> <HOST 1> <HOST 2>` where the hosts correspond to the specific server IDs running the server instances (i.e. order matters)

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
See our journal for details. We stipulate that usernames have max size 50 and messages have max size 262; as we use ASCII encoding, string length is equal to number of bytes used. Messages passed between the server and client will always first contain a 1-byte code determining the operation (for client requests) or status (for server responses). Codes correspond to distinct scenarios and are handled appropriately (see utils.py). Additional information is passed depending on the code, and in most cases consists as strings with ASCII encoding. We use the "|" character (also 1 byte) as a delimiter for message parsing. In particular, the additional information is:
- For login, register, logout, and delete requests, the client passes the username string. For search requests, the client passes the query string.
- For send requests, the client passes a string encoding with the form "sender|recipient|message".
- For login responses, if the user has unread messages, the server sends a 2-byte integer denoting the number of unread messages, and then the encoded messages. Each message has the form "sender|message".
- For search responses, if there are results, the server sends a 2-byte integer denoting the number of results, and then an encoded string of the results joined by "|"s.
- For incoming messages, the server sends the encoded message with the form "sender|message".

Try-excepts are used throughout to handle KeyboardInterrupts and other exceptions. The client and server code will attempt to log out on the event of a program exit. If a client loses connection with the server (e.g. the server shuts down), they will automatically exit.

## Primary-Secondary Replicas
In order to make our system distributed, we set up our system to support three server instances communicating with each other via server-to-server socket connections. We use a simple (and admittedly somewhat-hardcoded) primary/secondary replica setup, as we feel as it lends itself to a relatively straightforward implementation. One server acts as a primary replica, processing and executing client requests, while passing necessary updates to two replicas. When servers go down, new primaries are chosen as needed. State is stored as pickled dictionaries for each server instance. Specifically,
- **Replication**: The system operates among three server instances who communicate with each other, with given IDs 0, 1, and 2, via sockets. So that servers can easily differentiate whether or not they are communicating with clients or other servers through their sockets, each server instance communicates on different ports for server-to-server connections and client-to-server connections. Clients only communicate with the primary replica. 
- **Consistency**: To achieve fault tolerance in our setup, we try to enforce consistency. Whenever the primary replica processes a request that changes the state, it communicates these changes to the secondary replicas via server-to-server connections. State-changing operations include registering and deleting accounts (the set of registered users changes); logins; and sending undelivered messages (the message cache changes). Note that instantaneous sends and username searches do *not* count as state-changing queries; there is no need to propagate those queries to change replicas' states. We also don't communicate logouts, as our client code is set to silently re-login if they connect to a new primary.
- **2-Fault-Tolerance**: Since we assume crash/fail-stop failures occur, we need $2+1=3$ replicas running. As mentioned above, one serves as a replica and forwards information to the others so that all server instances have an updated view of the system state: which users exist, are logged in, and which messages are cached. In our implementation, we make use of the fact that *clients communicate with only the primary replica*: if a server receives client connections on their client-to-server socket, they will automatically know they have become the primary replica. Hence, the behavior for the primary replica (of sending state updates to other servers) can just be executed when handling a client connection. Clients will know a server will have gone down when their socket connection closes, in which case they can try opening new connections to the next-highest server ID. If needed, they will silently login.
- **Persistency**: We store the state of the system in memory and also as a pickled dictionary; we pickle after each state-changing operation (if efficiency is desired this could be done every certain number of operations instead). For our implementation, our state consists of a set of registered users, the message cache, and a timestamp. As mentioned, the primary communicates state changes to other servers. Upon server startup, each server instance will check for the existence of a pickled state dictionary and load it if so. To get the most recent state (as different servers might have been running for different times), servers also communicate their dictionaries to each other upon initialization, and the state with the most recent timestamp is universally adopted.
This of course happens behind the schemes, so users running client code are oblivious.

Our code is thoroughly documented and much of the protocol details are explained within. For more details on our implementation and a discussion of limitations, please also check out our design doc (linked at the top).
