import grpc
from concurrent import futures
import messageservice_pb2
import messageservice_pb2_grpc

class MessageServer(messageservice_pb2_grpc.MessageServiceServicer):
    def SendMessage(self, request, context):
        print(f"Sending message from user {request.sender} to user {request.receiver} with body {request.body}")
        context.set_code(grpc.StatusCode.OK)
        return messageservice_pb2.Status(code = 1)

    def GetMessages(self, request, context):
        print(f"Getting messages for user {request.receiver}")
        context.set_code(grpc.StatusCode.OK)
        exampleMessage = messageservice_pb2.Message(sender = "foo", receiver = "bar", body = "hello")
        return messageservice_pb2.MessageResponse(messages = [exampleMessage])
    
def serve():
    port = '22068'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messageservice_pb2_grpc.add_MessageServiceServicer_to_server(MessageServer(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
