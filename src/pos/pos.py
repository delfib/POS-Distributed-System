from enum import Enum
from src.pos.deposit import Deposit

class Role(Enum):
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    DOWN = "down"


class PointOfSale:
    def __init__(self, node_id: str):
        self.node_id : str = node_id
        
        # { node_id: "host:port" }
        self.peers : dict[str, str] = {}

        self.deposit = Deposit()
        self.role = Role.FOLLOWER
    
    def set_role(self, new_role: Role):
        self.role = new_role

    def add_peer(self, peer_id: str, address: str) -> None:
        """Connect to a new peer node."""
        if peer_id not in self.peers:
            self.peers[peer_id] = address
    
    def remove_peer(self, peer_id: str) -> None:
        """Disconnect from a peer node."""
        if peer_id in self.peers:
            del self.peers[peer_id]

    def broadcast_message(self, message: str) -> None:
        """Send a message to all connected peers."""
        for peer_id, address in self.peers.items():
            # Placeholder for actual network communication logic
            print(f"Sending message to {peer_id} at {address}: {message}")
