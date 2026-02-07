import threading

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from heartbeat import HeartbeatManager
from leader_election import LeaderElectionManager
from product_service import ProductService
from proto.pos_service_pb2 import (
    AbortUpdatePriceResponse,
    BuyProductResponse,
    CommitUpdatePriceResponse,
    ElectedRequest,
    ElectedResponse,
    ElectionResponse,
    GetProductPriceResponse,
    HeartbeatResponse,
    PrepareUpdatePriceResponse,
    ReloadDatabaseResponse,
    RequestStockResponse,
    UpdateProductPriceResponse,
)
from role import Role
from rpc_caller import RPCCaller


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
        self.role = role  
        self.peers = peers  # List of peers [(peer_id, host, port)]
        self.host = host  # Host where the node is running 
        self.port = port  # Port where the node is running
        self.leader_node = None  # (host, port)
        self.transaction_counter = 0  # Counter for transactions ids
        self.transaction_lock = threading.Lock()  # Lock for counter

        self.heartbeat_manager = HeartbeatManager(
            node_id=node_id,
            role=role,
            peers=peers,
            on_leader_failure=self._on_leader_failure,
        )

        self.product_service = ProductService(
            deposit=deposit,
            peers=peers,
        )

        self.leader_election_manager = LeaderElectionManager(
            node_id=node_id,
            peers=peers,
            on_leader_elected=self._on_leader_elected,
        )

    def start(self):
        """Start background services (heartbeats)."""
        self.heartbeat_manager.start()

    def stop(self):
        """Stop background services."""
        self.heartbeat_manager.stop()

    def _generate_transaction_id(self):
        """Generate a sequential transaction ID"""
        with self.transaction_lock:
            self.transaction_counter += 1

    def _is_leader(self) -> bool:
        """Check if this node is the leader"""
        return self.role == Role.LEADER

    def SendHeartbeat(self, request, context):
        """
        RPC invoked by the leader to signal liveness.
        Followers reset their heartbeat timeout upon receiving this.
        """
        self.heartbeat_manager.receive_heartbeat(request.leader_id)
        return HeartbeatResponse(success=True)

    def _on_leader_failure(self):
        """
        Callback triggered when the leader is considered failed.
        Stops heartbeat monitoring and starts a leader election.
        """
        print(f"[{self.node_id}] Starting leader election")
        self.heartbeat_manager.stop()
        self.leader_election_manager.start_election()

    def Election(self, request, context):
        """
        RPC used during leader election.
        Responds to election requests from peers.
        """
        should_reply = self.leader_election_manager.on_election(request.initiatior)
        return ElectionResponse(
            success=should_reply,
            peer_id=self.node_id if should_reply else "",
        )

    def Elected(self, request, context):
        """
        RPC received when a new leader has been elected.
        Updates local state and restarts heartbeat monitoring.
        """
        print(
            f"[{self.node_id}] Received Elected from new leader {request.new_leader_id}"
        )
        self.role = Role.FOLLOWER
        self.leader_node = (request.new_leader_host, request.new_leader_port)
        self.leader_election_manager.on_elected()  # Signal election manager
        self.heartbeat_manager.restart(self.role)  # restart heartbeat threads
        return ElectedResponse(success=True)

    def _on_leader_elected(self, new_leader_id):
        """
        Callback triggered when this node becomes the leader.
        Notifies all peers and starts sending heartbeats.
        """
        print(f"[{self.node_id}] Becoming the new leader")
        self.role = Role.LEADER

        # First broadcast Elected to all peers before starting heartbeats
        for _, host, port in self.peers:
            RPCCaller.execute_rpc_call(
                host,
                port,
                "Elected",
                ElectedRequest(
                    new_leader_id=self.node_id,
                    new_leader_host=self.host,
                    new_leader_port=self.port,
                ),
                timeout=3.0,
            )

        # Start sending heartbeats as leader
        self.heartbeat_manager.restart(self.role)

    def GetProductPrice(self, request, context):
        """RPC to get product price"""
        product = self.product_service.get_product(request.product_id)
        if product is None:
            return GetProductPriceResponse(message="Product not found")
        return GetProductPriceResponse(
            product_id=product.id, name=product.name, price=product.price
        )

    def BuyProduct(self, request, context):
        """
        RPC to buy a product. May involve coordination with peer nodes if local stock
        is insufficient.
        """
        success, quantity_sold, message = self.product_service.buy_product(
            request.product_id, request.quantity
        )
        return BuyProductResponse(
            success=success, quantity_sold=quantity_sold, message=message
        )

    def RequestStock(self, request, context):
        """
        RPC invoked by peers to request stock from this node.
        """
        provided = self.product_service.request_stock(
            request.product_id, request.quantity
        )
        return RequestStockResponse(quantity_provided=provided)

    def UpdateProductPrice(self, request, context):
        """
        RPC to update a product price. If this node is not the leader, the request is forwarded.
        """
        if not self._is_leader():
            return self._forward_to_leader(request)

        transaction_id = self._generate_transaction_id()

        # Phase 1: Prepare
        if not self.product_service._prepare_price_update(
            transaction_id, request.product_id, request.new_price
        ):
            return UpdateProductPriceResponse(
                success=False, message="Transaction aborted."
            )

        # Phase 2: Commit
        self.product_service._commit_price_update(transaction_id)

        return UpdateProductPriceResponse(
            success=True,
            message=f"Price updated successfully to ${request.new_price} (Transaction: {transaction_id})",
        )

    def _forward_to_leader(self, request):
        """Forward a price update request to the current leader."""
        if self.leader_node is None:
            return UpdateProductPriceResponse(
                success=False, message="Leader unknown, cannot process request"
            )

        leader_host, leader_port = self.leader_node
        success, response = RPCCaller.execute_rpc_call(
            leader_host,
            leader_port,
            "UpdateProductPrice",  # Method name as string
            request,
            timeout=10.0,
        )

        if success:
            return response
        else:
            return UpdateProductPriceResponse(
                success=False, message="Failed to contact leader."
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
        """Phase 2: Commit price update"""
        return CommitUpdatePriceResponse(
            success=self.deposit.commit_price_change(request.transaction_id)
        )

    def AbortUpdatePrice(self, request, context):
        """Abort a pending price update transaction."""
        return AbortUpdatePriceResponse(
            success=self.deposit.abort_price_change(request.transaction_id)
        )

    def ReloadDatabase(self, request, context):
        """
        RPC to reload the database from disk.
        """
        success = self.deposit.reload_database()
        if success:
            print(f"[{self.node_id}] Database reloaded from disk")
            return ReloadDatabaseResponse(
                success=True, message="Database reloaded successfully from disk"
            )
        else:
            return ReloadDatabaseResponse(
                success=False, message="Failed to reload database"
            )