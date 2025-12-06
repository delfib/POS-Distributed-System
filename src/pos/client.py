from __future__ import annotations

from typing import Optional

from .deposit import Product
from .pos import PointOfSale, Role


class Client:
    def __init__(self, connected_pos: Optional[PointOfSale] = None):
        self.connected_pos = connected_pos

    def connect(self, point_of_sale: PointOfSale) -> None:
        self.connected_pos = point_of_sale

    def buy_item(
        self, product_id: int, quantity: int, pos: Optional[PointOfSale] = None
    ) -> bool:
        """Buy a specified quantity of a product starting from the given POS."""
        point_of_sale = pos or self.connected_pos
        if not point_of_sale:
            raise ValueError("No point of sale available for the client.")

        if point_of_sale.role == Role.DOWN:
            print(f"POS {point_of_sale.node_id} is down. Cannot process purchase.")
            return False

        return point_of_sale.sell_product(product_id, quantity)

    def get_item(
        self, product_id: int, pos: Optional[PointOfSale] = None
    ) -> Optional[Product]:
        """Retrieve product information (price & stock) from the POS network."""
        point_of_sale = pos or self.connected_pos
        if not point_of_sale:
            raise ValueError("No point of sale available for the client.")
        return point_of_sale.query_product(product_id)
