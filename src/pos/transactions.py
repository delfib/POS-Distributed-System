import json
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

    def sell_product(self, product_id: int, quantity: int) -> bool:
        """Try to fulfill a sale locally. If not enough stock, ask peers.
        First peer that returns ok=True completes the sale."""
        if self.deposit.sell_product(product_id, quantity):
            print(f"[POS {self.node_id}] sold {quantity} of product {product_id} locally")
            return True

        print(f"[POS {self.node_id}] not enough stock to complete the sale; contacting peers...")

        request = {
            "type": "SELL_REQUEST",
            "product_id": product_id,
            "quantity": quantity,
            "sender": self.node_id
        }

        # TODO PeerManager.broadcast MUST return peer replies
        responses = self.peerManager.broadcast(json.dumps(request))
        """ assuming this responds with a dictionary of replies:
        {
            "peer1": {"ok": True, "response": {...}},
            "peer2": {"ok": False, "response": {...}},
        }
        """

         # Choose the first peer that accepted the sale
        for peer, result in responses.items():
            if result.get("ok") and result["response"].get("ok"):
                print(f"[POS {self.node_id}] peer {peer} completed the sale.")
                return True

        print(f"[POS {self.node_id}] sale failed: no peer had enough stock.")
        return False