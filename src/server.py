import time
import argparse
import json
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
    parser.add_argument(
        "--id",
        required=True,
        help="Node ID (e.g. POS1)"
    )
    return parser.parse_args()


# --------------------------------------------------
# Main entry point
# --------------------------------------------------
def main():
    args = parse_args()
    node_id = args.id

    # Load cluster configuration
    with open("config.json") as f:
        cluster = json.load(f)

    if node_id not in cluster:
        raise ValueError(f"Unknown node id {node_id}")

    node_cfg = cluster[node_id]

    host = node_cfg["host"]
    port = node_cfg["port"]
    db_path = node_cfg["db"]
    role = (
        Role.LEADER
        if node_cfg["role"] == "leader"
        else Role.FOLLOWER
    )

    # Create deposit (node-local state)
    deposit = Deposit(database_path=db_path)

    # Find leader address
    leader_address = None
    for cfg in cluster.values():
        if cfg["role"] == "leader":
            leader_address = (cfg["host"], cfg["port"])
            break

    # All peers except myself
    peers = [
        (cfg["host"], cfg["port"])
        for nid, cfg in cluster.items()
        if nid != node_id
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

    # IMPORTANT: start background tasks (heartbeats)
    node.start()

    print(f"gRPC server started on port {port} ({node_id} - {role.name})")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\nShutting down {node_id}...")
        node.stop()
        server.stop(0)


if __name__ == "__main__":
    main()
