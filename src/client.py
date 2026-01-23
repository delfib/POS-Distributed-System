import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from proto.pos_service_pb2 import (
    GetProductPriceRequest,
    BuyProductRequest,
    UpdateProductPriceRequest,
)


def test_price_operations():
    """Test getting and updating product prices"""
    print("=" * 60)
    print("Testing Price Operations")
    print("=" * 60)
    
    # Connect to POS1 (the leader)
    channel = grpc.insecure_channel("localhost:50051")
    stub = pos_service_pb2_grpc.POSStub(channel)

    # Get current price
    print("\n[1] Getting current price of product 1...")
    request = GetProductPriceRequest(product_id=1)
    response = stub.GetProductPrice(request)

    if response.message:
        print(f"   Error: {response.message}")
    else:
        print(f"   Product {response.product_id} - {response.name}: ${response.price}")

    # Update price (as leader)
    print("\n[2] Updating price of product 1 to $25 (via leader - POS1)...")
    update_request = UpdateProductPriceRequest(product_id=1, new_price=25)
    update_response = stub.UpdateProductPrice(update_request)
    
    print(f"   Success: {update_response.success}")
    print(f"   Message: {update_response.message}")

    # Verify price was updated
    print("\n[3] Verifying price was updated...")
    response = stub.GetProductPrice(request)
    print(f"   Product {response.product_id} - {response.name}: ${response.price}")

    channel.close()


def test_forward_to_leader():
    """Test forwarding price update from follower to leader"""
    print("\n" + "=" * 60)
    print("Testing Forward to Leader")
    print("=" * 60)
    
    # Connect to POS2 (a follower)
    channel = grpc.insecure_channel("localhost:50052")
    stub = pos_service_pb2_grpc.POSStub(channel)

    print("\n[1] Requesting price update via follower (POS2)...")
    print("   (This should be forwarded to the leader)")
    
    update_request = UpdateProductPriceRequest(product_id=1, new_price=9)
    update_response = stub.UpdateProductPrice(update_request)
    
    print(f"   Success: {update_response.success}")
    print(f"   Message: {update_response.message}")

    # Verify on the follower itself
    print("\n[2] Verifying price on follower (POS2)...")
    price_request = GetProductPriceRequest(product_id=1)
    response = stub.GetProductPrice(price_request)
    print(f"   Product {response.product_id} - {response.name}: ${response.price}")

    channel.close()


def test_buy_product():
    """Test buying products"""
    print("\n" + "=" * 60)
    print("Testing Buy Product")
    print("=" * 60)
    
    channel = grpc.insecure_channel("localhost:50051")
    stub = pos_service_pb2_grpc.POSStub(channel)

    print("\n[1] Attempting to buy 5 units of product 1...")
    buy_request = BuyProductRequest(product_id=1, quantity=5)
    buy_response = stub.BuyProduct(buy_request)

    print(f"   Success: {buy_response.success}")
    print(f"   Quantity sold: {buy_response.quantity_sold}")
    print(f"   Message: {buy_response.message}")

    channel.close()


def test_all_nodes_see_same_price():
    """Verify all nodes have the same price after update"""
    print("\n" + "=" * 60)
    print("Testing Price Consistency Across All Nodes")
    print("=" * 60)
    
    nodes = [
        ("POS1", "localhost", 50051),
        ("POS2", "localhost", 50052),
        ("POS3", "localhost", 50053),
    ]

    print("\n[1] Checking price on all nodes before update...")
    for node_name, host, port in nodes:
        channel = grpc.insecure_channel(f"{host}:{port}")
        stub = pos_service_pb2_grpc.POSStub(channel)
        
        request = GetProductPriceRequest(product_id=1)
        response = stub.GetProductPrice(request)
        print(f"   {node_name}: ${response.price}")
        
        channel.close()

    # Update price via leader
    print("\n[2] Updating price to $9 via leader...")
    channel = grpc.insecure_channel("localhost:50051")
    stub = pos_service_pb2_grpc.POSStub(channel)
    update_request = UpdateProductPriceRequest(product_id=1, new_price=25)
    update_response = stub.UpdateProductPrice(update_request)
    print(f"   {update_response.message}")
    channel.close()

    print("\n[3] Checking price on all nodes after update...")
    for node_name, host, port in nodes:
        channel = grpc.insecure_channel(f"{host}:{port}")
        stub = pos_service_pb2_grpc.POSStub(channel)
        
        request = GetProductPriceRequest(product_id=1)
        response = stub.GetProductPrice(request)
        print(f"   {node_name}: ${response.price}")
        
        channel.close()


def run():
    try:
        # test_price_operations()
        # test_forward_to_leader()
        # test_all_nodes_see_same_price()
        test_buy_product()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except grpc.RpcError as e:
        print(f"\nError: {e}")
        print("Make sure all servers are running!")


if __name__ == "__main__":
    run()