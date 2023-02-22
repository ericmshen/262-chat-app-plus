# 262-chat-app
## Dev Journal
See [here](https://docs.google.com/document/d/1pVqevcvZ9id7NcvimFF1evuONkPZ04kvvgWlIEtMIzE/edit?usp=sharing).
## Vanilla Sockets
### Installation
Ensure you've got the `socket` and `threading` modules already!

### Running
The server code must be running on a device before the client code can be run (on the same wifi network). 

To run the server code:
- change into the `sockets` directory by typing `cd sockets`
- type `python3 server.py` and click "enter"
- you can specify an optional port to run on as an argument

To run the client code:
- change into the `sockets` directory by typing `cd sockets`
- copy the strings next to "host" printed in the terminal of the computer running the server code (ex: `dhcp-10-250-12-215.harvard.edu`) and the "port" (ex: `22067`)
- type `python3 client.py {host} {port}` where `{host}` and `{port}` are the values copied in the previous step

To use the client code:
- try typing any of the commands: register, login, search, send, logout, delete, quit
- you must be logged in to send, logout, or delete
- after typing commands, you will be prompted to enter further details, if applicable
- incoming messages and results will be printed as they come; be warned that this might interrupt your input

To quit the client, either type `quit` into the terminal or press the `Ctrl+C` keys. To quit the server, press the `Ctrl+C` keys. Note that there may be multiple clients running at any given time but only one server.

## gRPC
### Installation
Using pip:
- `pip install grpcio`
- `pip install protobuf`

Using conda (recommended for Mac M1 users):
- `conda install grpcio`
- `conda install -c anaconda protobuf`

If you want to modify the code, optionally install `grpcio-tools`.

### Running
The server code must be running on a device before the client code can be run (on the same wifi network). 

To run the server code:
- change into the `grpc_impl` directory by typing `cd grpc_impl`
- type `python3 grpc_server.py` and click "enter"
- you can specify an optional port to run on as an argument

To run the client code:
- change into the `grpc_impl` directory by typing `cd grpc_impl`
- copy the strings next to "host" printed in the terminal of the computer running the server code (ex: `dhcp-10-250-12-215.harvard.edu`) and the "port" (ex: `22068`)
- type `python3 grpc_client.py {host} {port}` where `{host}` and `{port}` are the values copied in the previous step

You can run the client code analogously.

To quit the client, either type `quit` into the terminal or press the `Ctrl+C` keys. To quit the server, press the `Ctrl+C` keys. Note that there may be multiple clients running at any given time but only one server.