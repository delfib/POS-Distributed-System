import threading
from dataclasses import dataclass
from typing import Dict, Iterable, Optional


@dataclass
class Product:
    id: int
    name: str
    price: float
    quantity: int = 0


DEFAULT_PRODUCTS: Dict[int, Product] = {
    1: Product(1, "Apple", 0.5, 10),
    2: Product(2, "Banana", 0.3, 15),
    3: Product(3, "Orange", 0.7, 12),
}


def _clone_products(products: Dict[int, Product]) -> Dict[int, Product]:
    """Create in-memory copies so each deposit is isolated."""
    return {
        product_id: Product(
            id=product.id,
            name=product.name,
            price=product.price,
            quantity=product.quantity,
        )
        for product_id, product in products.items()
    }


class Deposit:
    def __init__(self, products: Optional[Dict[int, Product]] = None):
        catalog = products or DEFAULT_PRODUCTS
        self._items: Dict[int, Product] = _clone_products(catalog)
        self._lock = threading.Lock()

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
            return True
