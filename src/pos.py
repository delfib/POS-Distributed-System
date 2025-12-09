import random
import threading
import time

import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from proto.pos_service_pb2 import (
    AppendEntriesRequest,
    AppendEntriesResponse,
    BuyProductRequest,
    BuyProductResponse,
    GetProductPriceResponse,
    RequestVoteRequest,
    RequestVoteResponse,
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

        # Raft state
        self.state_lock = threading.Lock()
        self.current_term = 0
        self.voted_for = None
        self.leader_id = None
        self.heartbeat_interval = 1.0
        self.election_timeout_range = (2.0, 4.0)
        self._election_deadline = time.monotonic()
        self._stop_event = threading.Event()
        self._election_thread = threading.Thread(
            target=self._run_election_timer, daemon=True
        )
        self._heartbeat_thread = threading.Thread(
            target=self._run_heartbeat, daemon=True
        )

    def start(self):
        """Start background Raft tasks."""
        with self.state_lock:
            self._reset_election_deadline()
        if not self._election_thread.is_alive():
            self._election_thread.start()
        if not self._heartbeat_thread.is_alive():
            self._heartbeat_thread.start()

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
            leader_hint = (
                f"Current leader: {self.leader_id}"
                if self.leader_id
                else "Leader unknown"
            )
            return UpdateProductPriceResponse(
                message=f"Not authorized: Only the leader can update prices. {leader_hint}"
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

    #####################################################################################
    # Raft RPCs
    #####################################################################################

    def RequestVote(self, request, context):
        with self.state_lock:
            if request.term < self.current_term:
                return RequestVoteResponse(term=self.current_term, vote_granted=False)

            if request.term > self.current_term:
                self._become_follower(request.term)

            can_vote = self.voted_for in (None, request.candidate_id)
            if can_vote:
                self.voted_for = request.candidate_id
                self._reset_election_deadline()
            return RequestVoteResponse(term=self.current_term, vote_granted=can_vote)

    def AppendEntries(self, request, context):
        with self.state_lock:
            if request.term < self.current_term:
                return AppendEntriesResponse(term=self.current_term, success=False)
            if request.term >= self.current_term:
                if request.term > self.current_term:
                    self.current_term = request.term
                self._become_follower(request.term, request.leader_id)
            return AppendEntriesResponse(term=self.current_term, success=True)

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

    #####################################################################################
    # Raft helpers
    #####################################################################################

    def _reset_election_deadline(self):
        self._election_deadline = time.monotonic() + random.uniform(
            *self.election_timeout_range
        )

    def _become_follower(self, term: int, leader_id: str | None = None):
        self.role = Role.FOLLOWER
        self.current_term = term
        self.voted_for = None
        self.leader_id = leader_id
        self._reset_election_deadline()

    def _quorum_size(self) -> int:
        return (len(self.peers) + 1) // 2 + 1

    def _run_election_timer(self):
        while not self._stop_event.is_set():
            time.sleep(0.1)
            with self.state_lock:
                if self.role == Role.LEADER:
                    self._reset_election_deadline()
                    continue
                should_start = time.monotonic() >= self._election_deadline
            if should_start:
                self._start_election()

    def _start_election(self):
        with self.state_lock:
            self.current_term += 1
            term = self.current_term
            self.role = Role.CANDIDATE
            self.voted_for = self.node_id
            self.leader_id = None
            self._reset_election_deadline()
            print(f"Node {self.node_id} starting election for term {term}")

        votes = 1  # vote for self
        for peer in self.peers:
            response = self._request_vote_from_peer(peer, term)
            if response is None:
                continue
            with self.state_lock:
                if response.term > self.current_term:
                    print(
                        f"Node {self.node_id} found higher term {response.term} from peer; stepping down."
                    )
                    self._become_follower(response.term)
                    return
                still_candidate = (
                    self.role == Role.CANDIDATE and term == self.current_term
                )
            if not still_candidate:
                return
            if response.vote_granted:
                votes += 1

        with self.state_lock:
            if self.role == Role.CANDIDATE and votes >= self._quorum_size():
                self.role = Role.LEADER
                self.leader_id = self.node_id
                print(
                    f"Node {self.node_id} became leader for term {term} with {votes} votes."
                )
            else:
                print(
                    f"Node {self.node_id} failed to win election for term {term} ({votes} votes)."
                )

    def _request_vote_from_peer(self, peer, term: int):
        host, port = peer
        try:
            channel = grpc.insecure_channel(f"{host}:{port}")
            stub = pos_service_pb2_grpc.POSStub(channel)
            request = RequestVoteRequest(term=term, candidate_id=self.node_id)
            return stub.RequestVote(request, timeout=1.0)
        except Exception as exc:
            print(
                f"Node {self.node_id} failed to request vote from {host}:{port}: {exc}"
            )
            return None

    def _run_heartbeat(self):
        while not self._stop_event.is_set():
            with self.state_lock:
                is_leader = self.role == Role.LEADER
                term = self.current_term
            if not is_leader:
                time.sleep(0.2)
                continue

            for peer in self.peers:
                self._send_heartbeat_to_peer(peer, term)
            time.sleep(self.heartbeat_interval)

    def _send_heartbeat_to_peer(self, peer, term: int):
        host, port = peer
        try:
            channel = grpc.insecure_channel(f"{host}:{port}")
            stub = pos_service_pb2_grpc.POSStub(channel)
            request = AppendEntriesRequest(term=term, leader_id=self.node_id)
            response = stub.AppendEntries(request, timeout=1.0)
            with self.state_lock:
                if response.term > self.current_term:
                    print(
                        f"Node {self.node_id} discovered higher term {response.term} during heartbeat; stepping down."
                    )
                    self._become_follower(response.term)
        except Exception as exc:
            print(
                f"Node {self.node_id} failed to send heartbeat to {host}:{port}: {exc}"
            )
