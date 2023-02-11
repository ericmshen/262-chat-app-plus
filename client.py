import socket
import sys

PORT = 22067  # The port used by the server

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <host>")
    sys.exit(1)
    
HOST = sys.argv[1]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)

print(f"Received {data!r}")