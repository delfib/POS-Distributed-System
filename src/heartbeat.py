import random
import threading
import time
from typing import Callable, List, Tuple

from role import Role

HEARTBEAT_INTERVAL = 2.0  # how often leader sends heartbeats
HEARTBEAT_TIMEOUT_MIN = 5.0  # follower minimum wait time
HEARTBEAT_TIMEOUT_MAX = 10.0  # follower maximum wait time


class HeartbeatManager:
    """
    Gestiona la lógica de heartbeats para un nodo distribuido.

    - Si es LEADER: envía heartbeats periódicos a los followers
    - Si es FOLLOWER: monitorea heartbeats del leader y detecta fallas
    """

    def __init__(
        self,
        node_id: str,
        role: Role,
        peers: List[Tuple[str, int]],
        send_heartbeat_to_peer: Callable[[str, int], None],
        on_leader_failure: Callable[[], None],
    ):
        self.node_id = node_id
        self.role = role
        self.peers = peers
        self._send_heartbeat_to_peer = send_heartbeat_to_peer
        self._on_leader_failure = on_leader_failure

        self.last_heartbeat_time = time.time()
        self.heartbeat_timeout = self._random_timeout()
        self.running = False

    def _is_leader(self) -> bool:
        return self.role == Role.LEADER

    def _random_timeout(self) -> float:
        return random.uniform(HEARTBEAT_TIMEOUT_MIN, HEARTBEAT_TIMEOUT_MAX)

    def start(self):
        """Inicia los threads de heartbeat según el rol del nodo."""
        if self.running:
            return

        self.running = True

        if self._is_leader():
            threading.Thread(target=self._sender_loop, daemon=True).start()
        else:
            threading.Thread(target=self._watcher_loop, daemon=True).start()

    def stop(self):
        """Detiene los threads de heartbeat."""
        self.running = False

    def receive_heartbeat(self, leader_id: str):
        """Llamado cuando se recibe un heartbeat del leader."""
        print(f"[{self.node_id} ({self.role})] Heartbeat received from {leader_id}")
        self.last_heartbeat_time = time.time()
        self.heartbeat_timeout = self._random_timeout()

    def _sender_loop(self):
        """Loop del leader: envía heartbeats periódicamente a todos los peers."""
        while self.running:
            for peer_host, peer_port in self.peers:
                self._send_heartbeat_to_peer(peer_host, peer_port)

            print(f"[{self.node_id} ({self.role})] Sending heartbeats...")
            time.sleep(HEARTBEAT_INTERVAL)

    def _watcher_loop(self):
        """Loop del follower: detecta si el leader dejó de enviar heartbeats."""
        while self.running:
            time_elapsed = time.time() - self.last_heartbeat_time

            if time_elapsed > self.heartbeat_timeout:
                print(f"[{self.node_id}] Leader heartbeat missed")
                self._on_leader_failure()
                return

            time.sleep(0.5)
