import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from proto.pos_service_pb2 import (
    BuyProductRequest,
    BuyProductResponse,
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

    #####################################################################################
    # API Client Methods
    #####################################################################################

    def buy(self, product_id: int, quantity: int) -> bool:
        try:
            product_id_int = int(product_id)
        except ValueError:
            print(f"Invalid product id: {product_id}")
            return False

        print(
            f"Node {self.node_id} attempting to buy product {product_id_int} with quantity {quantity}"
        )
        is_in_my_stock = self.deposit.sell_product(product_id_int, quantity)
        if is_in_my_stock:
            return True

        # Ask peers
        print(f"Product {product_id_int} not in stock locally. Asking peers...")
        for peer in self.peers:
            host, port = peer  # Unpack host and port from the tuple
            try:
                print(f"Contacting peer at {host}:{port} for product {product_id_int}")
                # Abro una conexión con esa tienda
                channel = grpc.insecure_channel(f"{host}:{port}")
                print(f"Channel to {host}:{port} established.")
                # Creo un teléfono para hacer llamadas a esa tienda
                stub = pos_service_pb2_grpc.POSStub(channel)
                print(f"Stub to {host}:{port} created.")
                # Preparo la solicitud de compra
                buy_request = BuyProductRequest(
                    product_id=product_id_int,
                    quantity=quantity,
                    node_id_requesting=self.node_id,
                )
                print(f"Buy request for product {product_id_int} prepared.")
                # Hago la llamada y espero la respuesta
                response = stub.BuyProduct(buy_request)
                print(
                    f"Received response from peer {host}:{port}: success={response.success}, message={response.message}"
                )
                if response.success:
                    print(response.message)
                    print(
                        f"Purchase of product {product_id_int} successful from peer {host}:{port}"
                    )
                    return True
            except Exception as e:
                print(f"Error contacting peer {host}:{port}: {str(e)}")

    #####################################################################################
    # RPC Methods Implementation
    #####################################################################################

    def BuyProduct(self, request, context):
        """RPC to handle product purchase requests from clients or peers"""
        is_in_my_stock = self.deposit.sell_product(request.product_id, request.quantity)
        if is_in_my_stock:
            print(
                f"Product {request.product_id} sold {request.quantity} units. Peer: {request.node_id_requesting}"
            )
            return BuyProductResponse(
                success=True, message="Purchase successful", total_price=100.0
            )
        else:
            print(f"Product {request.product_id} not available for sale.")
            return BuyProductResponse(
                success=False, message="Product not available", total_price=-1.0
            )

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
