from typing import Optional

from src.pos.deposit import Deposit
from src.pos.peers import PeerManager


class TransactionManager:
    def __init__(
        self, node_id: str, peerManager: PeerManager, deposit: Optional[Deposit] = None
    ):
        self.deposit = deposit or Deposit()
        self.peerManager = peerManager
        self.node_id = node_id

    def sell_product(self, product_id: int, quantity: int) -> str:
        """Try to fulfill a sale locally. If not enough stock, ask peers.
        First peer that returns ok=True completes the sale."""
        if self.deposit.sell_product(product_id, quantity):
            print(
                f"[POS {self.node_id}] sold {quantity} of product {product_id} locally"
            )
            return True

        print(
            f"[POS {self.node_id}] not enough stock to complete the sale; contacting peers..."
        )

        return False

    def change_product_price(self, product_id: int, new_price: float) -> bool:
        status = {}
        if self.deposit.change_price(product_id, new_price):
            status["ok"] = True
        else:
            status["ok"] = False
            status["error"] = "product_not_found"
        return status
