from __future__ import annotations

import json
import socket
import threading
from typing import Optional

from src.pos.consensus import LeaderElection
from src.pos.deposit import Deposit
from src.pos.peers import PeerManager
from src.pos.role import Role
from src.pos.transactions import TransactionManager


class PointOfSale:
    def __init__(
        self,
        node_id: str,
        host: str = "127.0.0.1",
        port: int = 0,
        deposit: Optional[Deposit] = None,
    ):
        self.node_id: str = node_id
        self.role = Role.FOLLOWER
        self.host = host
        self.port = port
        self.peers = PeerManager(host, port, {})
        self.deposit = deposit or Deposit()
        self.transactions = TransactionManager(node_id, self.peers, self.deposit)
        self.consensus = LeaderElection()
        self.socket: Optional[socket.socket] = None

    def set_role(self, new_role: Role):
        self.role = new_role

    @property
    def is_online(self) -> bool:
        return self.role != Role.DOWN

    def start(self):
        print(f"[*] Listening on {self.host}:{self.port}")
        self.socket = self._create_server_socket(self.host, self.port)
        try:
            while self.socket:
                cli_socket, cli_address = self.socket.accept()
                print(f"[+] Connection from {cli_address}")
                threading.Thread(
                    target=self.handle_message, args=(), daemon=True
                ).start()
        except Exception as e:
            raise Exception(f"Server error: {e}")
        finally:
            if self.socket:
                self.socket.close()
                self.socket = None

    def handle_message(self, message: str):
        msg_type = message.get("type")
        try:
            if msg_type == "BUY_PRODUCT":
                return self._handle_buy_product(message)
            elif msg_type == "UPDATE_PRICE":
                return self.handle_price_update(message)
            else:
                print("Type of message unrecognized")
        except Exception as e:
            raise Exception(f"Error handling message: {e}")

    def handle_incoming_message(self, msg_json: str):
        msg = json.loads(msg_json)

        if msg["type"] == "SELL_REQUEST":
            product_id = msg["product_id"]
            quantity = msg["quantity"]

            ok = self.deposit.sell_product(product_id, quantity)

            return {
                "type": "SELL_RESPONSE",
                "ok": ok,
                "product_id": product_id,
                "quantity": quantity,
            }

        if msg["type"] == "PRICE_UPDATE":
            pid = msg["product_id"]
            price = msg["new_price"]

            updated = self.deposit.change_price(pid, price)
            print(f"[POS {self.node_id}] Updated price of {pid} to {price}")

            return {"ok": updated}

        return {"ok": False, "error": "unknown_message_type"}

    def handle_price_update(self, message: dict):
        # Only leader can update prices
        if self.role != Role.LEADER:
            return {"ok": False, "error": "not_leader"}

        pid = message["product_id"]
        new_price = message["new_price"]

        # Update leader’s own price
        ok = self.deposit.change_price(pid, new_price)

        if not ok:
            return {"ok": False, "error": "product_not_found"}

        # Broadcast update to followers
        update_msg = json.dumps(
            {
                "type": "PRICE_UPDATE",
                "product_id": pid,
                "new_price": new_price,
                "sender": self.node_id,
            }
        )

        print(f"[LEADER {self.node_id}] Broadcasting new price for product {pid}")

        self.peers.broadcast(update_msg)

        return {"ok": True}

    def _create_server_socket(self, host: str, port: int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(5)
        return sock

    def _handle_buy_product(self, message: str):
        product_id = message["product_id"]
        quantity = message["quantity"]

        print(f"Client is trying to buy {product_id} for amount: {quantity}")
        result = self.transactions.sell_product(product_id, quantity)
        return result
