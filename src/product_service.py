from typing import List, Tuple

from deposit import Deposit
from proto.pos_service_pb2 import RequestStockRequest
from rpc_caller import RPCCaller


class ProductService:
    """
    Gestiona la lógica de productos: consultar precios, comprar y solicitar stock.
    """

    def __init__(
        self,
        deposit: Deposit,
        peers: List[Tuple[str, int]],
    ):
        self.deposit = deposit
        self.peers = peers

    def get_product_price(self, product_id: int):
        """Obtiene el precio de un producto."""
        return self.deposit.get_product(product_id)

    def buy_product(self, product_id: int, requested_qty: int) -> Tuple[bool, int, str]:
        """
        Intenta comprar un producto, coordinando con peers si es necesario.

        Returns:
            (success, quantity_sold, message)
        """
        product = self.deposit.get_product(product_id)
        if product is None:
            return False, 0, "Product not found"

        remaining = self.deposit.sell_product(product_id, requested_qty)

        # Si no hay suficiente stock local, pedir a los peers
        if remaining > 0:
            remaining = self._request_stock_from_peers(product_id, remaining)

        total_sold = requested_qty - remaining

        if total_sold > 0:
            return True, total_sold, f"Successfully sold {total_sold} units"
        else:
            return False, 0, "Product not available in any node"

    def request_stock(self, product_id: int, requested_qty: int) -> int:
        """
        Responde a una solicitud de stock de otro peer.

        Returns:
            Cantidad proporcionada.
        """
        remaining = self.deposit.sell_product(product_id, requested_qty)
        return requested_qty - remaining

    def _request_stock_from_peers(self, product_id: int, remaining: int) -> int:
        """Solicita stock a los peers hasta cubrir la cantidad necesaria."""
        for peer_host, peer_port in self.peers:
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
