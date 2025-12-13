import random
import threading
import time

import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from proto.pos_service_pb2 import (
    GetProductPriceResponse,
    RequestStockRequest,
    RequestStockResponse,
    BuyProductResponse 
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
    
    def BuyProduct(self, request, context):
        """RPC to buy a product, coordinating with peers if needed"""
        product_id = request.product_id
        requested_qty = request.quantity

        product = self.deposit.get_product(product_id)
        if product is None:
            return BuyProductResponse(success=False, quantity_sold=0, message="Product not found")
        
        remaining = self.deposit.sell_product(product_id, requested_qty)
        
        if remaining > 0:
            for peer_host, peer_port in self.peers:
                if remaining <= 0:
                    break
                try:
                    channel = grpc.insecure_channel(f"{peer_host}:{peer_port}")
                    stub = pos_service_pb2_grpc.POSStub(channel)
                    
                    request_stock = RequestStockRequest(product_id=product_id,quantity=remaining)
                    response = stub.RequestStock(request_stock, timeout=5.0)
            
                    remaining -= response.quantity_provided
        
                    channel.close()
                    
                except grpc.RpcError as e:
                    print(f"[{self.node_id}] Failed to contact peer {peer_host}:{peer_port}: {e}")
                    continue
        
        total_sold = requested_qty - remaining
        if total_sold > 0:
            message = f"Successfully sold {total_sold} units"
            return BuyProductResponse(success=True, quantity_sold=total_sold, message=message)
        else:
            return BuyProductResponse(success=False, quantity_sold=0, message="Product not available in any node")
    

    def RequestStock(self, request, context):
        """RPC called by peers to request stock from this node"""
        product_id = request.product_id
        requested_qty = request.quantity
    
        remaining = self.deposit.sell_product(product_id, requested_qty)
        provided = requested_qty - remaining
        
        return RequestStockResponse(quantity_provided=provided)