from typing import Optional

from src.pos.deposit import Deposit


class ProductStockManager:
    def __init__(self, node_id: str, deposit: Optional[Deposit] = None):
        self.deposit = deposit or Deposit()
        self.node_id = node_id

    def sell_product(self, product_id: int, quantity: int) -> str:
        """Attempt to sell a product from the deposit."""
        if self.deposit.sell_product(product_id, quantity):
            return True
        return False
