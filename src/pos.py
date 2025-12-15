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
    BuyProductResponse,
    PrepareUpdatePriceRequest,
    PrepareUpdatePriceResponse,
    UpdateProductPriceResponse,
    CommitUpdatePriceRequest,
    CommitUpdatePriceResponse,
    AbortUpdatePriceRequest,
    AbortUpdatePriceResponse 
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
        leader_node: None
    ):
        self.deposit = deposit
        self.node_id = node_id
        self.role = role  # Set the role as passed (LEADER or FOLLOWER)
        self.peers = peers  # List of peers to notify
        self.host = host  # Host where the node is running (IP or hostname)
        self.port = port  # Port where the node is running
        self.leader_node = leader_node   # (host, port)
        self.transaction_counter = 0  # Counter for transactions
        self.transaction_lock = threading.Lock()  # Lock for counter

    def _generate_transaction_id(self):
        """Generate a sequential transaction ID"""
        with self.transaction_lock:
            self.transaction_counter += 1
    
    def _is_leader(self) -> bool:
        """Check if this node is the leader"""
        return self.role == Role.LEADER

    def _contact_peer(self, peer_host: str, peer_port: int, method_name: str, request_obj, timeout=5.0):
        """Contact a peer and execute an RPC call. Returns (success: bool, response: Any)"""
        try:
            channel = grpc.insecure_channel(f"{peer_host}:{peer_port}")
            stub = pos_service_pb2_grpc.POSStub(channel)
            
            method = getattr(stub, method_name)
            response = method(request_obj, timeout=timeout)

            channel.close()
            return True, response
        except grpc.RpcError as e:
            print(f"[{self.node_id}] Failed to contact {peer_host}:{peer_port}: {e}")
            return False, None


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
                
                success, response = self._contact_peer(
                    peer_host,
                    peer_port,
                    "RequestStock",
                    RequestStockRequest(product_id=product_id, quantity=remaining),
                    timeout=5.0
                )
                
                if success and response:
                    remaining -= response.quantity_provided
        

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
    

    def UpdateProductPrice(self, request, context):
        """RPC to update product price - forwards to leader if not leader"""
        if not self._is_leader():
            return self._forward_to_leader(request)

        transaction_id = self._generate_transaction_id()
        
        # Phase 1: Prepare
        if not self._prepare_phase(transaction_id, request.product_id, request.new_price):
            return UpdateProductPriceResponse(success=False, message="Transaction aborted.")
    
        # Phase 2: Commit 
        self._commit_phase(transaction_id)
        
        return UpdateProductPriceResponse(  
            success=True,
            message=f"Price updated successfully to ${request.new_price} (Transaction: {transaction_id})"
        )


    def _forward_to_leader(self, request):
        """Forward price update request to the leader"""
        if self.leader_node is None:
            return UpdateProductPriceResponse(success=False, message="Leader unknown, cannot process request")

        leader_host, leader_port = self.leader_node
        success, response = self._contact_peer(
            leader_host,
            leader_port,
            "UpdateProductPrice",  # Method name as string
            request,
            timeout=10.0
        )

        if success:
            return response
        else:
            return UpdateProductPriceResponse(success=False, message=f"Failed to contact leader.")


    def _prepare_phase(self, transaction_id: str, product_id: int, new_price: float) -> bool:
        """ Prepares all nodes to commit. Returns True if all nodes are ready, False otherwise. """
        product = self.deposit.get_product(product_id)
        new_version = product.version + 1
        if not self.deposit.prepare_price_change(transaction_id, product_id, new_price, new_version):
            return False
        
        all_ready = True
        for peer_host, peer_port in self.peers:
            success, response = self._contact_peer(
                peer_host,
                peer_port,
                "PrepareUpdatePrice",
                PrepareUpdatePriceRequest(product_id=product_id, new_price=new_price, transaction_id=transaction_id, version=new_version),
                timeout=5.0
            )

            if not success or not response or not response.ready:
                all_ready = False
                # break

        if all_ready:
            return True
        else:
            self._abort_phase(transaction_id)
            return False
 

    def _commit_phase(self, transaction_id: str):
        """Commit the transaction on all nodes"""
        self.deposit.commit_price_change(transaction_id)

        for peer_host, peer_port in self.peers:
            self._contact_peer(
                peer_host,
                peer_port,
                "CommitUpdatePrice",
                CommitUpdatePriceRequest(transaction_id=transaction_id),
                timeout=5.0
            )

    def _abort_phase(self, transaction_id: str):
        """Abort the transaction on all nodes"""
        self.deposit.abort_price_change(transaction_id)

        for peer_host, peer_port in self.peers:
            self._contact_peer(
                peer_host,
                peer_port,
                "AbortUpdatePrice",
                AbortUpdatePriceRequest(transaction_id=transaction_id),
                timeout=5.0
            )

    def PrepareUpdatePrice(self, request, context):
        """Phase 1: Prepare to update price"""
        ready = self.deposit.prepare_price_change(
            request.transaction_id,
            request.product_id,
            request.new_price,
            request.version,
        )
        
        message = "Ready to commit" if ready else "Product not found"
        return PrepareUpdatePriceResponse(ready=ready, message=message)


    def CommitUpdatePrice(self, request, context):
        """Phase 2: Commit the price update"""
        transaction_id = request.transaction_id

        success = self.deposit.commit_price_change(transaction_id)
        return CommitUpdatePriceResponse(success=success)


    def AbortUpdatePrice(self, request, context):
        """Phase 2: Abort the price update"""
        transaction_id = request.transaction_id

        success = self.deposit.abort_price_change(transaction_id)
        return AbortUpdatePriceResponse(success=success)