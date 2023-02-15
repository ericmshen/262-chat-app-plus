import grpc
import messageservice_pb2
import messageservice_pb2_grpc
import sys

def run():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <host>")
        sys.exit(1)
    host = sys.argv[1]
    port = "22068"
    
    print("Starting gRPC client...")
    
    with grpc.insecure_channel(host + ":" + port) as channel:
        print(f"Connected to {host}:{port}")
        stub = messageservice_pb2_grpc.MessageServiceStub(channel)
        # test send message
        print("Sending register...")
        response = stub.Register(messageservice_pb2.UsernameRequest(username="poo"))
        print(f"Client received status code: {response.statusCode}")

if __name__ == '__main__':
    run()
