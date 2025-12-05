from enum import Enum
from src.pos.deposit import *

class Role(Enum):
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    DOWN = "down"

class PointOfSale:
    def __init__(self, node_id: str):
        self.node_id : str = node_id
        
        # { node_id: "host:port" }
        # List
        self.peers : list[PointOfSale] = []

        self.deposit = Deposit()
        self.role = Role.FOLLOWER


    def set_deposit(self, deposit: Deposit):
        self.deposit = deposit
 
    def set_role(self, new_role: Role):
        self.role = new_role

    def add_peer(self, peer) -> None:
        """Connect to a new peer node."""
        self.peers.append(peer)
    
    def remove_peer(self, peer_id: str) -> None:
        """Disconnect from a peer node."""
        self.peers.remove(peer_id)

    def broadcast_message(self, message: str) -> None:
        """Send a message to all connected peers."""
        for peer in self.peers:
            print(f"Sending message to {peer.node_id}: {message}")

    def sell_product(self, product_id : int, quantity : int) -> bool:
        
        if self.deposit.sell_product(product_id, quantity):
            print(f"Sold {quantity} of {product_id} locally")
            return True
        print("Not enough stock, searching with peers")

        for peer in self.peers:
            if peer.deposit.sell_product(product_id, quantity):
                print(f"Sold {quantity} of {product_id} with POS {peer.node_id}")
                return True

        print("Not enough overall stock to complete sale.")
        return False