import argparse
import json
import os
import time
from concurrent import futures

import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from pos import POSServicer
from role import Role

def parse_args():
    parser = argparse.ArgumentParser(description="Start a POS node")
    parser.add_argument("--id", type=int, required=True, help="Node ID (e.g. 1)")
    return parser.parse_args()


def server_setup(node):
    """
    Create and configure the gRPC server for this node.
    The server exposes the POS gRPC service and listens on the node's port.

    Args:
        node (POSServicer): The POS node instance implementing the gRPC service.

    Returns:
        grpc.Server: Configured gRPC server instance.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node, server)
    server.add_insecure_port(f"[::]:{node.port}")

    return server


def node_setup(node_id):
    """
    Initialize a POS node based on configuration.
    Args:
        node_id (int): Identifier of the node to start.
    Returns:
        POSServicer: Fully initialized POS node.
    """
    config_file = os.getenv("CONFIG_FILE", "src/config.json")
    with open(config_file) as f:
        config = json.load(f)

    nodes = config["nodes"]

    node_cfg = next((n for n in nodes if n["id"] == node_id), None)
    if node_cfg is None:
        raise ValueError(f"Unknown node id {node_id}")

    host = node_cfg["host"]
    port = node_cfg["port"]
    db_path = node_cfg["db"]

    deposit = Deposit(database_path=db_path)

    # Build list of peer nodes (exclude self). Each peer is identified by (id, host, port)
    peers = [(n["id"], n["host"], n["port"]) for n in nodes if n["id"] != node_id]


    # Initial role is always FOLLOWER
    # If a leader already exists, this node will receive heartbeats and remain a follower.
    # If no leader exists, heartbeat timeout will trigger an election.
    role = Role.FOLLOWER

    node = POSServicer(
        deposit=deposit,
        node_id=node_id,
        role=role,
        peers=peers,
        host=host,
        port=port,
    )

    return node


def main():
    args = parse_args()
    node_id = args.id

    node = node_setup(node_id)

    server = server_setup(node)
    server.start()

    node.start()

    print(
        f"gRPC server started on port {node.port} (node {node_id} - {node.role.name})"
    )

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\nShutting down node {node_id}...")
        node.stop()
        server.stop(0)


if __name__ == "__main__":
    main()