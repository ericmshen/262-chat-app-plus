# 262-chat-app
## Vanilla Sockets
### Installation
No installations needed!

### Running
The server code must be running on a device before the client code can be run (on the same wifi network). 

To run the server code:
- change into the `sockets` directory by typing `cd sockets`
- type `python3 server.py` and click "enter"

To run the client code:
- change into the `sockets` directory by typing `cd sockets`
- copy the strings next to "host" printed in the terminal of the computer running the server code (ex: `dhcp-10-250-12-215.harvard.edu`) and the "port" (ex: `22067`)
- type `python3 client.py {host} {port}` where `{host}` and `{port}` are the values copied in the previous step

To quit the client, either type `quit` into the terminal or press the `Cmd+Q` keys. To quit the server, press the `Cmd+Q` keys. Note that there may be multiple clients running at any given time but only one server.

## gRPC
### Installation
Using pip:
- `pip install grpcio`
- `pip install protobuf`

Using conda (recommended for Max M1 users):
- `conda install grpcio`
- `conda install -c anaconda protobuf`

### Running
The server code must be running on a device before the client code can be run (on the same wifi network). 

To run the server code:
- change into the `grpc` directory by typing `cd grpc`
- type `python3 grpc_server.py` and click "enter"

To run the client code:
- change into the `grpc` directory by typing `cd grpc`
- copy the strings next to "host" printed in the terminal of the computer running the server code (ex: `dhcp-10-250-12-215.harvard.edu`) and the "port" (ex: `22068`)
- type `python3 grpc_client.py {host} {port}` where `{host}` and `{port}` are the values copied in the previous step

To quit the client, either type `quit` into the terminal or press the `Cmd+Q` keys. To quit the server, press the `Cmd+Q` keys. Note that there may be multiple clients running at any given time but only one server.