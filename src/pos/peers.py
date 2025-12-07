import socket
from typing import Dict


class PeerManager:
    def __init__(self, addres: str, port: int, peers: Dict[str, int]) -> None:
        self.port: int = port
        self.addres: str = addres
        self.peers: Dict[str, int] = peers
        # self.message_queue = []

    def add_peer(self, addres: str, port: int) -> None:
        self.peers[addres] = port

    def remove_peer(self, address: str) -> None:
        self.peers.pop(address, None)

    # Broadcast a message to all peers
    def broadcast(self, msg_json: str) -> None:
        for address, port in self.peers.items():
            data = self.send(message, product_id, address, port)
            return data

    #def send(self, message: str, product_id: str, address: str, port: int) -> None:
    def send(self, msg_jsom: str) -> None:
        # Implement sending logic here socket communication, etc.?

        msg = f"Product ID: {product_id}\nMessage: {message}"

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((address, port))
            s.sendall(msg.encode("utf-8"))
            data = s.recv(1024)
            return data.decode("utf-8")

    #def receive(self, message: str, product_id: str, address: str, port: int) -> None:
    def receive(self, msg_json: str) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((address, port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                print("Connected by", addr)
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(
                        f"Received message for product {product_id}: {data.decode('utf-8')}"
                    )
                    msg = self.response(message, product_id, address, port)
                    conn.sendall(msg.encode("utf-8"))

    #def response(self, message: str, product_id: str, address: str, port: int) -> None:
    def response(self, msg_json: str) -> None:
        return "Acknowledged"


#    def response(self, message: str, product_id: str, address: str, port: int) -> None:
#
#        return "Acknowledged"
