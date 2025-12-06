from __future__ import annotations

import socket
import sys
from pathlib import Path
from typing import Optional

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))

from argsparser.parser import ArgsParser
from pos.consensus import LeaderElection
from pos.deposit import Deposit, Product
from pos.peers import PeerManager
from pos.role import Role
from pos.transactions import TransactionManager


class PointOfSale:
    def __init__(
        self,
        node_id: str,
        host: str = "127.0.0.1",
        port: int = 0,
        deposit: Optional[Deposit] = None,
    ):
        self.node_id: str = node_id
        self.role = Role.FOLLOWER
        self.host = host
        self.port = port
        self.peers = PeerManager(host, port, {})
        self.deposit = deposit or Deposit()
        self.transactions = TransactionManager(node_id, self.peers, self.deposit)
        self.consensus = LeaderElection()
        self.socket: Optional[socket.socket] = None

    def set_role(self, new_role: Role):
        self.role = new_role

    @property
    def is_online(self) -> bool:
        return self.role != Role.DOWN

    def add_peer(
        self,
        peer: Optional[PointOfSale] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        """Connect to a new peer node."""
        if peer and peer.node_id == self.node_id:
            return

        peer_key: Optional[str] = None
        if peer:
            self._peer_nodes[peer.node_id] = peer
            peer_key = peer.node_id

        if endpoint:
            host, port = self._parse_endpoint(endpoint)
            self.peers.add_peer(host, port)
            peer_key = peer_key or endpoint
            self._peer_endpoints[peer_key] = (host, port)

    def remove_peer(self, peer_id: str) -> None:
        """Disconnect from a peer node."""
        self._peer_nodes.pop(peer_id, None)
        endpoint = self._peer_endpoints.pop(peer_id, None)
        if endpoint:
            self.peers.remove_peer(endpoint[0])

    def broadcast_message(self, message: str) -> None:
        """Send a message to all connected peers."""
        for peer_id, peer in self._peer_nodes.items():
            print(f"[{self.node_id}] -> [{peer_id}] {message}")

    def sell_product(self, product_id: int, quantity: int) -> bool:
        """Try to fulfill a sale locally, then ask peers in order."""
        if not self.is_online:
            print(f"POS {self.node_id} unavailable for sales.")
            return False

        if self.deposit.sell_product(product_id, quantity):
            print(f"POS {self.node_id} sold {quantity} of product {product_id} locally")
            return True

        print(f"POS {self.node_id} searching stock with peers")
        for peer in self._peer_nodes.values():
            if peer.fulfill_remote_sale(product_id, quantity):
                print(
                    f"POS {self.node_id} sold {quantity} of {product_id} "
                    f"via peer {peer.node_id}"
                )
                return True

        print(f"POS {self.node_id} lacks sufficient stock to complete sale")
        return False

    def fulfill_remote_sale(self, product_id: int, quantity: int) -> bool:
        """Used by peers to request a sale from our deposit."""
        if not self.is_online:
            return False
        return self.deposit.sell_product(product_id, quantity)

    def update_price(self, product_id: int, price: float) -> bool:
        """Leaders propagate price changes to keep the catalog consistent."""
        if self.role != Role.LEADER:
            print(f"POS {self.node_id} is not leader, ignoring price update request")
            return False

        if not self.deposit.change_price(product_id, price):
            print(
                f"POS {self.node_id} cannot update price for unknown product {product_id}"
            )
            return False

        for peer in self._peer_nodes.values():
            peer.receive_price_update(product_id, price)
        return True

    def receive_price_update(self, product_id: int, price: float) -> None:
        """Apply a price change coming from the leader."""
        self.deposit.change_price(product_id, price)

    def query_product(self, product_id: int) -> Optional[Product]:
        """Return a product snapshot from this node or any peer."""
        product = self.deposit.get_product(product_id)
        if product:
            return product

        for peer in self._peer_nodes.values():
            if not peer.is_online:
                continue
            product = peer.deposit.get_product(product_id)
            if product:
                return product
        return None

    def start(self):
        print(f"[*] Listening on {self.host}:{self.port}")
        self.socket = self._create_server_socket(self.host, self.port)
        try:
            while self.socket:
                cli_socket, cli_address = self.socket.accept()
                print(f"[+] Connection from {cli_address}")
                # threading.Thread(target=self.handle_message, args=(), daemon=True).start()
        except Exception as e:
            raise Exception(f"Server error: {e}")
        finally:
            if self.socket:
                self.socket.close()
                self.socket = None

    def _create_server_socket(self, host: str, port: int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(5)
        return sock


if __name__ == "__main__":
    args = ArgsParser.build_parser()
    pos = PointOfSale(node_id=args.node_id, host=args.host, port=args.port)
    pos.start()