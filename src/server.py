import time
from concurrent import futures

import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from pos import POSServicer
from role import Role


def main():
    # Initialize the deposits (databases)
    deposit1 = Deposit(database_path="db/db1.json")  
    deposit2 = Deposit(database_path="db/db2.json")  
    deposit3 = Deposit(database_path="db/db3.json")  

    # Cluster configuration
    peers = {
        "POS1": ("localhost", 50051),
        "POS2": ("localhost", 50052),
        "POS3": ("localhost", 50053),
    }

    # Define the leader (for now, POS1 is the leader)
    leader_address = peers["POS1"]

    # Create POS nodes
    node_1 = POSServicer(
        deposit=deposit1,
        node_id="POS1",
        role=Role.LEADER,  # POS1 is the leader
        peers=[peers["POS2"], peers["POS3"]],
        host="localhost",
        port=50051,
        leader_node=leader_address  # Leader knows itself
    )
    
    node_2 = POSServicer(
        deposit=deposit2,
        node_id="POS2",
        role=Role.FOLLOWER,  # POS2 is a follower
        peers=[peers["POS1"], peers["POS3"]],
        host="localhost",
        port=50052,
        leader_node=leader_address  # Follower knows who the leader is
    )
    
    node_3 = POSServicer(
        deposit=deposit3,
        node_id="POS3",
        role=Role.FOLLOWER,  # POS3 is a follower
        peers=[peers["POS1"], peers["POS2"]],
        host="localhost",
        port=50053,
        leader_node=leader_address  # Follower knows who the leader is
    )

    # Start 3 servers, each on different ports
    server1 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_1, server1)
    server1.add_insecure_port("[::]:50051")
    server1.start()
    print("gRPC server started on port 50051 (POS1 - LEADER)")

    server2 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_2, server2)
    server2.add_insecure_port("[::]:50052")
    server2.start()
    print("gRPC server started on port 50052 (POS2 - FOLLOWER)")

    server3 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_3, server3)
    server3.add_insecure_port("[::]:50053")
    server3.start()
    print("gRPC server started on port 50053 (POS3 - FOLLOWER)")

    try:
        while True:
            time.sleep(86400)  # Keep all servers running
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        server1.stop(0)
        server2.stop(0)
        server3.stop(0)


if __name__ == "__main__":
    main()