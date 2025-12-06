from __future__ import annotations

import socket
from typing import Optional

from src.pos.consensus import LeaderElection
from src.pos.deposit import Deposit
from src.pos.peers import PeerManager
from src.pos.role import Role
from src.pos.transactions import TransactionManager


class Handler:
    pass


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

    def handle_message(self, message: str):
        msg_type = message.get("type")
        try:
            if msg_type == "BUY_PRODUCT":
                
            else:
                print("Type of message unrecognized")
        except Exception as e:
            raise Exception(f"Error handling message: {e}")

    def start(self):
        print(f"[*] Listening on {self.host}:{self.port}")
        self.socket = self._create_server_socket(self.host, self.port)
        try:
            while self.socket:
                cli_socket, cli_address = self.socket.accept()
                print(f"[+] Connection from {cli_address}")
                # threading.Thread(target=self.handle_message, args=(), daemon=True).start()
        except Exception as e:
            raise Exception(f"Server error: {e}")
        finally:
            if self.socket:
                self.socket.close()
                self.socket = None

    def _create_server_socket(self, host: str, port: int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(5)
        return sock
