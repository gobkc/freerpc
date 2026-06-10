from services.grpc_service import dynamic_grpc_call

# Unary 调用
response = dynamic_grpc_call(
    proto_path="./protos/helloworld.proto",
    service_name="Greeter",
    method_name="SayHello",
    rpc_type="unary",
    host="localhost:50051",
    request_dict={"name": "GTK User"},
)
print(response)

# Server Streaming 调用
for chunk in dynamic_grpc_call(
    proto_path="./protos/helloworld.proto",
    service_name="Greeter",
    method_name="SayHellos",
    rpc_type="server_streaming",
    host="localhost:50051",
    request_dict={"name": "User", "count": 10},
):
    print(chunk)


# Client Streaming 调用
def request_generator():
    for i in range(3):
        yield {"data": i, "timestamp": "2024-01-01T00:00:00Z"}


summary = dynamic_grpc_call(
    proto_path="./protos/data.proto",
    service_name="DataService",
    method_name="UploadBatch",
    rpc_type="client_streaming",
    host="localhost:50051",
    request_dict={},
    request_stream=request_generator(),
)
