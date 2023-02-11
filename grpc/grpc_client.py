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
        print("Sending message...")
        response = stub.SendMessage(messageservice_pb2.Message(sender = "foo", receiver = "bar", body = "hello"))
        print(f"Client received status code: {response.code}")
        # test get message
        print("Getting messages...")
        response = stub.GetMessages(messageservice_pb2.MessageRequest(receiver = "bar"))
        print(f"Client received messages: {str(response.messages)}")

if __name__ == '__main__':
    run()
