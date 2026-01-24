import argparse
import json
import time
from concurrent import futures

import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from pos import POSServicer
from role import Role


# --------------------------------------------------
# CLI arguments
# --------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Start a POS node")
    parser.add_argument("--id", type=int, required=True, help="Node ID (e.g. 1)")
    return parser.parse_args()


# --------------------------------------------------
# Main entry point
# --------------------------------------------------
def main():
    args = parse_args()
    node_id = args.id

    # Load cluster configuration
    with open("src/config.json") as f:
        config = json.load(f)

    nodes = config["nodes"]

    # Find my node config
    node_cfg = next((n for n in nodes if n["id"] == node_id), None)
    if node_cfg is None:
        raise ValueError(f"Unknown node id {node_id}")

    host = node_cfg["host"]
    port = node_cfg["port"]
    db_path = node_cfg["db"]
    role = Role.LEADER if node_cfg["role"] == "leader" else Role.FOLLOWER

    # Create deposit (node-local state)
    deposit = Deposit(database_path=db_path)

    # Find leader address
    leader_cfg = next((n for n in nodes if n["role"] == "leader"), None)
    leader_address = (
        (leader_cfg["host"], leader_cfg["port"])
        if leader_cfg is not None
        else None
    )

    # All peers except myself (id, host, port)
    peers = [
        (n["id"], n["host"], n["port"])
        for n in nodes
        if n["id"] != node_id
    ]

    # Create POS node
    node = POSServicer(
        deposit=deposit,
        node_id=node_id,
        role=role,
        peers=peers,
        host=host,
        port=port,
        leader_node=leader_address,
    )

    # Start gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()

    # Start background tasks (heartbeats, etc.)
    node.start()

    print(f"gRPC server started on port {port} (node {node_id} - {role.name})")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\nShutting down node {node_id}...")
        node.stop()
        server.stop(0)


if __name__ == "__main__":
    main()
