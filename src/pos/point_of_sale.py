from __future__ import annotations

import socket
import threading

from src.pos.deposit import Deposit
from src.pos.transactions import ProductStockManager


class PointOfSale:
    def __init__(
        self, node_id: str, host: str, port: int, db_path: str = "src/db/db1.json"
    ) -> None:
        self.node_id = node_id
        self.host = host
        self.port = port + 1
        # Peers in the distributed system
        self.peers: dict[str, PointOfSale] = {}
        self.deposit = Deposit(db_path)
        self.product_manager = ProductStockManager(node_id, self.deposit)

    def start(self) -> None:
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print(f"Starting TCP server on {self.host}:{self.port}")
            s.bind((self.host, self.port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    conn.send(data.upper())

    def buy(self, product_id: str, quantity: int) -> bool:
        try:
            product_id_int = int(product_id)
        except ValueError:
            print(f"Invalid product id: {product_id}")
            return False

        is_in_my_stock = self.product_manager.sell_product(product_id_int, quantity)
        if is_in_my_stock:
            return True
        # Ask peers
        for peer_id, peer in self.peers.items():
            print(f"Asking peer {peer_id} for product {product_id_int}")
            target_host = peer.host if peer.host != "0.0.0.0" else "127.0.0.1"
            # establecer conexión con el peer
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((target_host, peer.port))
                    # enviar solicitud de compra
                    message = f"buy {product_id_int} {quantity}"
                    s.sendall(message.encode())
                    # recibir respuesta
                    data = s.recv(1024)
                    response = data.decode().strip()
                    print(f"Received response from {peer_id}: {response}")
                    if response == "SUCCESS":
                        return True
            except (ConnectionRefusedError, socket.timeout, OSError) as exc:
                print(f"Peer {peer_id} unavailable: {exc}")
        return False
