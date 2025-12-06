from typing import Optional

from pos.deposit import Deposit
from pos.peers import PeerManager

class TransactionManager:
    def __init__(self, node_id: str, peerManager: PeerManager, deposit: Optional[Deposit] = None):
        self.deposit = deposit or Deposit()
        self.peerManager = peerManager
        self.node_id = node_id

    def sell_product(self, product_id: int, quantity: int) -> bool:
        """Try to fulfill a sale locally, then ask peers in order."""
        if self.deposit.sell_product(product_id, quantity):
            print(f"POS {self.node_id} sold {quantity} of product {product_id} locally")
            return True

        print(f"POS {self.node_id} searching stock with peers")

        message = f"SELL_ITEM: id = {product_id}, quantity = {quantity}"
        self.peerManager.broadcast(message, product_id)

        # how does this node know the item was actually sold by another node?
        
        print(f"POS {self.node_id} lacks sufficient stock to complete sale")
        return False