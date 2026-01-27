from typing import List, Tuple

from deposit import Deposit
from proto.pos_service_pb2 import RequestStockRequest, PrepareUpdatePriceRequest, AbortUpdatePriceRequest, CommitUpdatePriceRequest
from rpc_caller import RPCCaller


class ProductService:
    """
    Manages product-related logic: purchases and stock updates.
    """

    def __init__(
        self,
        deposit: Deposit,
        peers: List[Tuple[str, int]],
    ):
        self.deposit = deposit
        self.peers = peers

    def get_product(self, product_id: int):
        """Gets a product by its id."""
        return self.deposit.get_product(product_id)

    def buy_product(self, product_id: int, requested_qty: int) -> Tuple[bool, int, str]:
        product = self.deposit.get_product(product_id)
        if product is None:
            return False, 0, "Product not found"

        remaining = self.deposit.sell_product(product_id, requested_qty)

        if remaining > 0:
            remaining = self._request_stock_from_peers(product_id, remaining)

        total_sold = requested_qty - remaining

        if total_sold > 0:
            return True, total_sold, f"Successfully sold {total_sold} units"
        else:
            return False, 0, "Product not available in any node"

    def request_stock(self, product_id: int, requested_qty: int) -> int:
        remaining = self.deposit.sell_product(product_id, requested_qty)
        return requested_qty - remaining

    def _request_stock_from_peers(self, product_id: int, remaining: int) -> int:
        for peer_id, peer_host, peer_port in self.peers:
            if remaining <= 0:
                break

            success, response = RPCCaller.execute_rpc_call(
                peer_host,
                peer_port,
                "RequestStock",
                RequestStockRequest(product_id=product_id, quantity=remaining),
                timeout=5.0,
            )

            if success and response:
                remaining -= response.quantity_provided

        return remaining
    
    def _prepare_price_update(
        self, transaction_id: str, product_id: int, new_price: float
    ) -> bool:
        """Prepares all nodes to commit. Returns True if all nodes are ready, False otherwise."""
        product = self.deposit.get_product(product_id)
        new_version = product.version + 1
        if not self.deposit.prepare_price_change(
            transaction_id, product_id, new_price, new_version
        ):
            return False

        all_ready = True
        for peer_id, peer_host, peer_port in self.peers:
            success, response = RPCCaller.execute_rpc_call(
                peer_host,
                peer_port,
                "PrepareUpdatePrice",
                PrepareUpdatePriceRequest(
                    product_id=product_id,
                    new_price=new_price,
                    transaction_id=transaction_id,
                    version=new_version,
                ),
                timeout=5.0,
            )

            if not success or not response or not response.ready:
                all_ready = False
                # break

        if all_ready:
            return True
        else:
            self._abort_phase(transaction_id)
            return False
        
    

    def _commit_price_update(self, transaction_id: str):
        """Commit the transaction on all nodes"""
        self.deposit.commit_price_change(transaction_id)

        for peer_id, peer_host, peer_port in self.peers:
            RPCCaller.execute_rpc_call(
                peer_host,
                peer_port,
                "CommitUpdatePrice",
                CommitUpdatePriceRequest(transaction_id=transaction_id),
                timeout=5.0,
            )

    def _abort_price_update(self, transaction_id: str):
        """Abort the transaction on all nodes"""
        self.deposit.abort_price_change(transaction_id)

        for peer_id, peer_host, peer_port in self.peers:
            RPCCaller.execute_rpc_call(
                peer_host,
                peer_port,
                "AbortUpdatePrice",
                AbortUpdatePriceRequest(transaction_id=transaction_id),
                timeout=5.0,
            )