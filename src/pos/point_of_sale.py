from __future__ import annotations

from src.pos.deposit import Deposit
from src.pos.transactions import ProductStockManager


class PointOfSale:
    def __init__(self, node_id: str, host: str, port: int, db_path: str) -> None:
        self.node_id = node_id
        self.host = host
        self.port = port
        # Peers in the distributed system
        self.peers: dict[str, PointOfSale] = {
            "pos-2": PointOfSale("pos-2", "0.0.0.0", 8001, db_path="src/db/db2.json"),
            "pos-3": PointOfSale("pos-3", "0.0.0.0", 8002, db_path="src/db/db3.json"),
        }
        self.deposit = Deposit("src/db/db1.json")
        self.product_manager = ProductStockManager(node_id, self.deposit)

    def start(self) -> None:
        print(f"Point of Sale {self.node_id} started at {self.host}:{self.port}")

    def buy(self, product_id: str, quantity: int) -> bool:
        is_in_my_stock = self.product_manager.sell_product(product_id, quantity)
        if is_in_my_stock:
            return True
        # Ask peers
        for peer_id, peer in self.peers.items():
            # establecer conexión con el peer
            # enviar solicitud de compra
            # esperar respuesta
            # if peer_can_sell:
            #     return True
            pass
        return False
