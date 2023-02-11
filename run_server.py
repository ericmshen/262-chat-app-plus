
import sys
from server import Server

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <host> <port> <socket | gRPC>")
        sys.exit(1)
    
    host, port, conn = sys.argv[1], sys.argv[2], sys.argv[3]

    server = Server("127.0.0.1", 22067)
    server.run()
