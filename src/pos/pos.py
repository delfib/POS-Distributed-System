from __future__ import annotations

from typing import Optional

from pos.consensus import LeaderElection
from pos.peers import PeerManager
from pos.role import Role
from pos.transactions import TransactionManager

from .deposit import Deposit, Product


class PointOfSale:
    def __init__(self, node_id: str, deposit: Optional[Deposit] = None):
        self.node_id: str = node_id
        self.role = Role.FOLLOWER
        self.peers = PeerManager()
        self.transactions = TransactionManager(node_id, deposit)
        self.consensus = LeaderElection()

    def set_role(self, new_role: Role):
        self.role = new_role

    @property
    def is_online(self) -> bool:
        return self.role != Role.DOWN

    def add_peer(self, peer: PointOfSale, endpoint: Optional[str] = None) -> None:
        """Connect to a new peer node."""
        if peer.node_id == self.node_id:
            return
        self.peers.add_peer(peer.node_id, endpoint)

    def remove_peer(self, peer_id: str) -> None:
        """Disconnect from a peer node."""
        self.peers.remove_peer(peer_id)

    def broadcast_message(self, message: str) -> None:
        """Send a message to all connected peers."""
        for peer in self.peers.values():
            print(f"[{self.node_id}] -> [{peer.node.node_id}] {message}")

    def sell_product(self, product_id: int, quantity: int) -> bool:
        """Try to fulfill a sale locally, then ask peers in order."""
        if not self.is_online:
            print(f"POS {self.node_id} unavailable for sales.")
            return False

        if self.deposit.sell_product(product_id, quantity):
            print(f"POS {self.node_id} sold {quantity} of product {product_id} locally")
            return True

        print(f"POS {self.node_id} searching stock with peers")
        for peer in self.peers.values():
            if peer.node.fulfill_remote_sale(product_id, quantity):
                print(
                    f"POS {self.node_id} sold {quantity} of {product_id} "
                    f"via peer {peer.node.node_id}"
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

        for peer in self.peers.values():
            peer.node.receive_price_update(product_id, price)
        return True

    def receive_price_update(self, product_id: int, price: float) -> None:
        """Apply a price change coming from the leader."""
        self.deposit.change_price(product_id, price)

    def query_product(self, product_id: int) -> Optional[Product]:
        """Return a product snapshot from this node or any peer."""
        product = self.deposit.get_product(product_id)
        if product:
            return product

        for peer in self.peers.values():
            if not peer.node.is_online:
                continue
            product = peer.node.deposit.get_product(product_id)
            if product:
                return product
        return None
