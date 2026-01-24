import random
import threading
import time
from typing import List, Tuple

from proto.pos_service_pb2 import HeartbeatRequest
from role import Role
from rpc_caller import RPCCaller

HEARTBEAT_INTERVAL = 2.0  # how often leader sends heartbeats
HEARTBEAT_TIMEOUT_MIN = 5.0  # follower minimum wait time
HEARTBEAT_TIMEOUT_MAX = 10.0  # follower maximum wait time

class HeartbeatManager:
    """
    Handles the heartbeat logic for a node.

    - If the node is the LEADER: periodically sends heartbeats to followers
    - If the node is a FOLLOWER: monitors leader heartbeats and detects leader failure
    """
    def __init__(
        self,
        node_id: str,
        role: Role,
        peers: List[Tuple[str, int]],
        on_leader_failure: callable
    ):
        self.node_id = node_id
        self.role = role
        self.peers = peers
        self.on_leader_failure = on_leader_failure

        self.last_heartbeat_time = time.time()
        self.heartbeat_timeout = self._random_timeout()
        self.running = False

    def _is_leader(self) -> bool:
        return self.role == Role.LEADER

    def _random_timeout(self) -> float:
        return random.uniform(HEARTBEAT_TIMEOUT_MIN, HEARTBEAT_TIMEOUT_MAX)

    def start(self):
        """Initiates the heartbeat threads according to the node's role."""
        if self.running:
            return

        self.running = True

        if self._is_leader():
            threading.Thread(target=self._sender_loop, daemon=True).start()
        else:
            threading.Thread(target=self._watcher_loop, daemon=True).start()

    def stop(self):
        """Stops the heartbeat threads."""
        self.running = False

    def restart(self, new_role: Role):
        self.stop()
        self.role = new_role
        self.last_heartbeat_time = time.time()
        self.heartbeat_timeout = self._random_timeout()
        self.start()

    def receive_heartbeat(self, leader_id: str):
        """
        Handles an incoming heartbeat from the current leader.
        Updates the last heartbeat timestamp and resets the timeout.
        """
        print(f"[{self.node_id} ({self.role})] Heartbeat received from {leader_id}")
        self.last_heartbeat_time = time.time()
        self.heartbeat_timeout = self._random_timeout()

    def _sender_loop(self):
        """Periodically sends heartbeats to all the peers."""
        while self.running:
            for peer_id, peer_host, peer_port in self.peers:
                RPCCaller.execute_rpc_call(
                    peer_host,
                    peer_port,
                    "SendHeartbeat",
                    HeartbeatRequest(leader_id=self.node_id),
                    timeout=2.0,
                )
            print(f"[{self.node_id} ({self.role})] Sending heartbeats...")
            time.sleep(HEARTBEAT_INTERVAL)

    def _watcher_loop(self):
        """Detects if the leader stoped sending heartbeats."""
        while self.running:
            time_elapsed = time.time() - self.last_heartbeat_time

            if time_elapsed > self.heartbeat_timeout:
                print(f"[{self.node_id}] Leader heartbeat missed")
                self.on_leader_failure()
                return

            time.sleep(0.5)