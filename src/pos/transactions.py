from typing import Optional

from pos.deposit import Deposit


class TransactionManager:
    def __init__(self, node_id: str, deposit: Optional[Deposit] = None):
        self.deposit = deposit or Deposit()

    # sell product


    
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

