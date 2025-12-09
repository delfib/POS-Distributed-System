import json
import threading
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class Product:
    id: int
    name: str
    price: float
    quantity: int = 0


class Deposit:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._items = self._load_products(database_path) if database_path else {}
        self._lock = threading.Lock()

    def _load_products(self, database_path: str):
        with open(database_path) as f:
            data = json.load(f)
        return {int(pid): Product(**info) for pid, info in data.items()}

    def list_products(self) -> Iterable[Product]:
        with self._lock:
            return [
                Product(
                    id=product.id,
                    name=product.name,
                    price=product.price,
                    quantity=product.quantity,
                )
                for product in self._items.values()
            ]

    def get_product(self, product_id: int) -> Optional[Product]:
        with self._lock:
            product = self._items.get(product_id)
            if not product:
                return None
            return Product(
                id=product.id,
                name=product.name,
                price=product.price,
                quantity=product.quantity,
            )

    def add_stock(self, product_id: int, quantity: int) -> None:
        with self._lock:
            product = self._items.get(product_id)
            if product:
                product.quantity += quantity

    def sell_product(self, product_id: int, quantity: int) -> bool:
        with self._lock:
            product = self._items.get(product_id)
            if not product or product.quantity < quantity:
                return False
            product.quantity -= quantity
            return True

    def change_price(self, product_id: int, price: float) -> bool:
        with self._lock:
            product = self._items.get(product_id)
            if not product:
                return False
            product.price = price
            # Save the updated data back to the file
            self._save_products()
            return True

    def _save_products(self):
        with open(self.database_path, "w") as f:
            data = {pid: product.__dict__ for pid, product in self._items.items()}
            json.dump(data, f, indent=4)
