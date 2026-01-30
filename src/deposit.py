import json
import threading
from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass
class Product:
    id: int
    name: str
    price: float
    quantity: int = 0
    version: int = 0


class Deposit:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self._items = self._load_products(database_path) if database_path else {}
        self._lock = threading.Lock()
        self._pending_transactions: Dict[str, Dict] = {}

    def reload_database(self) -> bool:
        """
        Reloads the database from disk.
        Useful for development/testing when JSON files are modified manually.
        """
        with self._lock:
            try:
                self._items = self._load_products(self.database_path)
                return True
            except Exception as e:
                print(f"Error reloading database: {e}")
                return False

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
                    version=product.version,
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
                version=product.version,
            )

    def add_stock(self, product_id: int, quantity: int) -> None:
        with self._lock:
            product = self._items.get(product_id)
            if product:
                product.quantity += quantity
                self._save_products()

    def sell_product(self, product_id: int, requested_qty: int) -> int:
        """
        Attempt to sell `requested_qty` units of a product.
        Returns how many units could NOT be sold.
        """
        with self._lock:
            product = self._items.get(product_id)
            if not product:
                return requested_qty

            qty_available = product.quantity

            if qty_available >= requested_qty:
                product.quantity -= requested_qty
                self._save_products()
                return 0

            product.quantity = 0
            self._save_products()
            return requested_qty - qty_available

    def change_price(self, product_id: int, price: float) -> bool:
        with self._lock:
            product = self._items.get(product_id)
            if not product:
                return False
            product.price = price
            # Save the updated data back to the file
            self._save_products()
            return True

    def prepare_price_change(
        self, transaction_id: str, product_id: int, new_price: float, version: int
    ) -> bool:
        """Phase 1: Prepare to change price. Returns True if ready."""
        with self._lock:
            product = self._items.get(product_id)
            if not product:
                return False

            self._pending_transactions[transaction_id] = {
                "product_id": product_id,
                "new_price": new_price,
                "version": version,
            }
            return True

    def commit_price_change(self, transaction_id: str) -> bool:
        """Phase 2: Commit the price change."""
        with self._lock:
            transaction = self._pending_transactions[transaction_id]
            if not transaction:
                return False

            product = self._items.get(transaction["product_id"])

            if not product:
                del self._pending_transactions[transaction_id]
                return False

            incoming_version = transaction["version"]

            if incoming_version <= product.version:
                del self._pending_transactions[transaction_id]
                return False

            product.price = transaction["new_price"]
            product.version = incoming_version
            self._save_products()

            del self._pending_transactions[transaction_id]
            return True

    def abort_price_change(self, transaction_id: str) -> bool:
        """Phase 2: Abort the price change."""
        with self._lock:
            if transaction_id in self._pending_transactions:
                del self._pending_transactions[transaction_id]
            return True

    def _save_products(self):
        with open(self.database_path, "w") as f:
            data = {pid: product.__dict__ for pid, product in self._items.items()}
            json.dump(data, f, indent=4)
