import time
from concurrent import futures

import grpc
import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from proto.pos_service_pb2 import (
    GetProductPriceResponse,
    UpdateProductPriceRequest,
    UpdateProductPriceResponse,
)
from role import Role


class POSServicer(pos_service_pb2_grpc.POSServicer):
    def __init__(
        self,
        deposit: Deposit,
        node_id: str,
        role: Role,
        peers: list,
        host: str,
        port: int,
    ):
        self.deposit = deposit
        self.node_id = node_id
        self.role = role  # Set the role as passed (LEADER or FOLLOWER)
        self.peers = peers  # List of peers to notify
        self.host = host  # Host where the node is running (IP or hostname)
        self.port = port  # Port where the node is running

    def GetProductPrice(self, request, context):
        """RPC to get product price"""
        product = self.deposit.get_product(request.product_id)
        if product is None:
            return GetProductPriceResponse(message="Product not found")
        return GetProductPriceResponse(
            product_id=product.id, name=product.name, price=product.price
        )

    def UpdateProductPrice(self, request, context):
        """RPC to update product price (only the leader can do this)"""
        if self.role != Role.LEADER:
            return UpdateProductPriceResponse(
                message="Not authorized: Only the leader can update prices."
            )

        # The leader updates the price
        success = self.deposit.change_price(request.product_id, request.new_price)
        if success:
            print(
                f"Price for product {request.product_id} updated to {request.new_price}."
            )
            # Notify all peers (followers) of the price change
            self.notify_peers(request.product_id, request.new_price)
            return UpdateProductPriceResponse(
                success=True, message="Price updated successfully"
            )
        else:
            return UpdateProductPriceResponse(
                success=False, message="Product not found"
            )

    def notify_peers(self, product_id, new_price):
        """Send a gRPC request to all peers to update the product price"""
        for peer in self.peers:
            host, port = peer  # Unpack host and port from the tuple
            try:
                print(
                    f"Notifying peer at {host}:{port} to update price for product {product_id} to {new_price}"
                )
                # Notify peers via gRPC to update the price
                channel = grpc.insecure_channel(f"{host}:{port}")
                stub = pos_service_pb2_grpc.POSStub(channel)
                update_request = UpdateProductPriceRequest(
                    product_id=product_id, new_price=new_price
                )
                response = stub.NotifyPeersToUpdatePrice(update_request)
                if not response.success:
                    print(f"Failed to notify peer {host}:{port}: {response.message}")
            except Exception as e:
                print(f"Error notifying peer {host}:{port}: {str(e)}")

    def NotifyPeersToUpdatePrice(self, request, context):
        """RPC to handle price update notifications from the leader"""
        print(
            f"Peer {self.node_id} received price update for product {request.product_id} to {request.new_price}"
        )
        success = self.deposit.change_price(request.product_id, request.new_price)
        if success:
            return UpdateProductPriceResponse(
                success=True, message="Price updated successfully"
            )
        else:
            return UpdateProductPriceResponse(
                success=False, message="Product not found"
            )


def serve():
    # Initialize the deposit (database)
    deposit1 = Deposit(database_path="db/db1.json")  # Leader's database
    deposit2 = Deposit(database_path="db/db2.json")  # Follower 1's database
    deposit3 = Deposit(database_path="db/db3.json")  # Follower 2's database

    # Create POS nodes (hardcoded)
    # Pass the peer list as tuples (host, port)
    node_1 = POSServicer(
        deposit1,
        "POS1",
        Role.LEADER,
        [("localhost", 50052), ("localhost", 50053)],
        "localhost",
        50051,
    )
    node_2 = POSServicer(
        deposit2, "POS2", Role.FOLLOWER, [("localhost", 50051)], "localhost", 50052
    )
    node_3 = POSServicer(
        deposit3, "POS3", Role.FOLLOWER, [("localhost", 50051)], "localhost", 50053
    )

    # Start 3 servers, each on different ports
    server1 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_1, server1)
    server1.add_insecure_port("[::]:50051")  # Leader on port 50051
    server1.start()
    print("gRPC server started on port 50051 (Leader)")

    server2 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_2, server2)
    server2.add_insecure_port("[::]:50052")  # Follower 1 on port 50052
    server2.start()
    print("gRPC server started on port 50052 (Follower 1)")

    server3 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_3, server3)
    server3.add_insecure_port("[::]:50053")  # Follower 2 on port 50053
    server3.start()
    print("gRPC server started on port 50053 (Follower 2)")

    try:
        while True:
            time.sleep(86400)  # Keep all servers running
    except KeyboardInterrupt:
        server1.stop(0)
        server2.stop(0)
        server3.stop(0)


if __name__ == "__main__":
    serve()
