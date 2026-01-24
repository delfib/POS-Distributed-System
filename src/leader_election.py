import threading
import time
from rpc_caller import RPCCaller
from proto.pos_service_pb2 import ElectionRequest

# Time to wait for a higher node to declare itself leader
ELECTION_TIMEOUT = 5.0

class LeaderElectionManager:
    """
    Implements the Bully leader election algorithm.
    """
    def __init__(self, node_id: int, peers: list, on_leader_elected: callable):
        self.node_id = node_id
        self.peers = peers
        self.on_leader_elected = on_leader_elected

        self._lock = threading.Lock()
        self._election_in_progress = False
        self._received_elected = False  # Flag to track if we received an Elected message


    def start_election(self):
        """
        Starts a Bully election.
        """
        with self._lock:
            if self._election_in_progress:
                return
            self._election_in_progress = True
            self._received_elected = False

        print(f"[{self.node_id}] Starting Bully election")

        higher_peers = self._get_higher_peers()

        got_response = False

        for peer_id, peer_host, peer_port in higher_peers:
            success, response = RPCCaller.execute_rpc_call(
                peer_host,
                peer_port,
                "Election",
                ElectionRequest(initiatior=self.node_id),
                timeout=3.0,
            )
            if success and response and response.success:
                got_response = True

        if not got_response:
            # No higher peer answered, declares itself as the leader
            self._become_leader()
        else:
            # Wait for the higher node to complete its election and send Elected
            print(f"[{self.node_id}] Higher node exists, waiting for Elected message...")
            start_time = time.time()
            while time.time() - start_time < ELECTION_TIMEOUT:
                with self._lock:
                    if self._received_elected:
                        print(f"[{self.node_id}] Received Elected, election complete")
                        self._election_in_progress = False
                        return
                time.sleep(0.5)
            
            # Timeout: higher node failed to become leader, retry election
            print(f"[{self.node_id}] Timeout waiting for Elected, retrying election")
            with self._lock:
                self._election_in_progress = False
            self.start_election()
            return

        with self._lock:
            self._election_in_progress = False

    def on_election(self, initiator_id: str) -> bool:
        """
        Handles an incoming ELECTION message.
        Returns True if this node responds.
        """
        if self.node_id > initiator_id:
            print(f"[{self.node_id}] Election received from {initiator_id}, responding")
        
            threading.Thread(
                target=self.start_election,
                daemon=True
            ).start()

            return True

        return False

    def on_elected(self):
        """
        Called when this node receives an Elected message.
        Signals that a higher node has become leader.
        """
        with self._lock:
            self._received_elected = True
            self._election_in_progress = False

    def _get_higher_peers(self):
        """
        Returns peers with higher IDs than this node.
        """
        return [
            (peer_id, peer_host, peer_port)
            for peer_id, peer_host, peer_port in self.peers
            if peer_id > self.node_id
        ]

    def _become_leader(self):
        """
        Declares self as leader and broadcasts ELECTED.
        """
        print(f"[{self.node_id}] Becoming leader")
        self.on_leader_elected(self.node_id)