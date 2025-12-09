import grpc
import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from proto.pos_service_pb2 import GetProductPriceRequest, UpdateProductPriceRequest


def run():
    # Create a channel to connect to the server
    channel = grpc.insecure_channel("localhost:50051")
    stub = pos_service_pb2_grpc.POSStub(channel)

    # Create a request for product ID 2 (for example)
    request = GetProductPriceRequest(product_id=2)

    # Call the GetProductPrice method to get the current price
    response = stub.GetProductPrice(request)

    # Print the current product price
    if response.message:
        print("Error:", response.message)
    else:
        print(f"Product {response.product_id} - {response.name}: ${response.price}")

    # After getting the current price, let's update the price if needed
    # Create a request to update the price of product 2
    # Only the leader will be able to update the price
    new_price = 15000000000  # Set a new price for product 2
    update_request = UpdateProductPriceRequest(product_id=1, new_price=new_price)

    # Call the UpdateProductPrice method to update the price (this will only work if you're connecting to the leader)
    update_response = stub.UpdateProductPrice(update_request)

    # Print the result of the update request
    if update_response.success:
        print(
            f"Price for product {update_request.product_id} updated successfully to ${update_request.new_price}"
        )
    else:
        print("Failed to update price:", update_response.message)


if __name__ == "__main__":
    run()
