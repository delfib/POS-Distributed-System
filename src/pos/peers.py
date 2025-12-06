from typing import Dict


class PeerManager:
    def __init__(self, addres: str, port: int, peers: Dict[str, int]) -> None:
        self.port: int = port
        self.addres: str = addres
        self.peers: Dict[str, int] = peers
        self.message_queue = []

    def add_peer(self, addres: str, port: int) -> None:
        self.peers[addres] = port
        pass

    def remove_peer(self, address: str) -> None:
        self.peers.pop(address, None)
        pass

    def broadcast(
        self,
        message: str,
        product_id: str
    ) -> None:

        pass

    def send(
        self,
        message: str,
        product_id: str,
        address: str,
        port: int
    ) -> None:
        pass

    def receive(self) -> None:
        pass    

    def respond(
        self,
        message: str,
        product_id: str,
        address: str,
        port: int
    ) -> None:
        pass
