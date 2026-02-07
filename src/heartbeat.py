import random
import threading
import time
from typing import List, Tuple

import grpc

from proto.pos_service_pb2 import HeartbeatRequest
from role import Role
from rpc_caller import RPCCaller

HEARTBEAT_INTERVAL = 2.0  # how often leader sends heartbeats
HEARTBEAT_TIMEOUT_MIN = 5.0  # follower minimum wait time
HEARTBEAT_TIMEOUT_MAX = 10.0  # follower maximum wait time

class HeartbeatManager:
    """
    Manages heartbeat communication between nodes in the system.

    - If the node is the LEADER:
        * Periodically sends heartbeat messages to all peers
    - If the node is a FOLLOWER:
        * Monitors incoming heartbeats from the leader
        * Detects leader failure when heartbeats stop arriving
        * Triggers a leader election when failure is detected
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

        self._lock = threading.Lock()
        self._current_thread = None

    def _is_leader(self) -> bool:
        """Returns True if this node is currently the leader."""
        return self.role == Role.LEADER

    def _random_timeout(self) -> float:
        """Generates a randomized heartbeat timeout."""
        return random.uniform(HEARTBEAT_TIMEOUT_MIN, HEARTBEAT_TIMEOUT_MAX)

    def start(self):
        """Initiates the heartbeat threads according to the node's role."""
        with self._lock:
            if self.running:
                return

            self.running = True

            if self._is_leader():
                self._current_thread = threading.Thread(target=self._sender_loop, daemon=True)
            else:
                self._current_thread = threading.Thread(target=self._watcher_loop, daemon=True)
            
            self._current_thread.start()

    def stop(self):
        """
        Stops the heartbeat thread safely.
        Ensures threads terminate cleanly.
        """
        with self._lock:
            self.running = False
            thread = self._current_thread
            self._current_thread = None
        
        # Wait for thread to finish (outside lock to prevent deadlock)
        # Don't join if we're being called from the thread itself
        if thread and thread.is_alive() and thread != threading.current_thread():
            thread.join(timeout=2.0)

    def restart(self, new_role: Role):
        """Restarts heartbeat logic after a role change."""
        self.stop()
        with self._lock:
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
        """Leader loop: periodically sends heartbeats to all the peers."""
        while self.running and self._is_leader():
            for peer_id, peer_host, peer_port in self.peers:
                if not self.running or not self._is_leader():
                    break
                try:
                    RPCCaller.execute_rpc_call(
                        peer_host,
                        peer_port,
                        "SendHeartbeat",
                        HeartbeatRequest(leader_id=self.node_id),
                        timeout=2.0,
                    )
                except Exception as e:
                    print(f"[{self.node_id}] Failed to send heartbeat to {peer_id}: {e}")
            
            if self.running and self._is_leader():
                print(f"[{self.node_id} ({self.role})] Sending heartbeats...")
            time.sleep(HEARTBEAT_INTERVAL)

    def _watcher_loop(self):
        """Follower loop: detects if the leader stopped sending heartbeats."""
        while self.running:
            time_elapsed = time.time() - self.last_heartbeat_time

            if time_elapsed > self.heartbeat_timeout:
                print(f"[{self.node_id}] Leader heartbeat missed")
                self.on_leader_failure()
                return

            time.sleep(0.5)