import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from proto.pos_service_pb2 import (
    GetProductPriceRequest,
    BuyProductRequest,
)


def run():
    # Create a channel to connect to the server
    channel = grpc.insecure_channel("localhost:50051")
    stub = pos_service_pb2_grpc.POSStub(channel)

    # Get product price
    request = GetProductPriceRequest(product_id=1)
    response = stub.GetProductPrice(request)

    if response.message:
        print("Error:", response.message)
    else:
        print(f"Product {response.product_id} - {response.name}: ${response.price}")

    # Try to buy a product
    print("\n--- Attempting to buy 5 units of product 1 ---")
    buy_request = BuyProductRequest(product_id=1, quantity=5)
    buy_response = stub.BuyProduct(buy_request)

    print(f"Quantity sold: {buy_response.quantity_sold}")
    print(f"Message: {buy_response.message}")


if __name__ == "__main__":
    run()