import time
from concurrent import futures

import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from deposit import Deposit
from pos import POSServicer
from role import Role


def main():
    # Initialize the deposit (database)
    deposit1 = Deposit(database_path="src/db/db1.json")  # Leader's database
    deposit2 = Deposit(database_path="src/db/db2.json")  # Follower 1's database
    deposit3 = Deposit(database_path="src/db/db3.json")  # Follower 2's database

    # Create POS nodes (hardcoded)
    # Pass the peer list as tuples (host, port)
    node_1 = POSServicer(
        deposit1,
        "POS1",
        Role.LEADER,
        [("localhost", 50052), ("localhost", 50053)],
        "localhost",
        50051,
    )
    node_2 = POSServicer(
        deposit2, "POS2", Role.FOLLOWER, [("localhost", 50051)], "localhost", 50052
    )
    node_3 = POSServicer(
        deposit3, "POS3", Role.FOLLOWER, [("localhost", 50051)], "localhost", 50053
    )

    # Start 3 servers, each on different ports
    server1 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_1, server1)
    server1.add_insecure_port("[::]:50051")  # Leader on port 50051
    server1.start()
    print("gRPC server started on port 50051 (Leader)")

    server2 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_2, server2)
    server2.add_insecure_port("[::]:50052")  # Follower 1 on port 50052
    server2.start()
    print("gRPC server started on port 50052 (Follower 1)")

    server3 = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pos_service_pb2_grpc.add_POSServicer_to_server(node_3, server3)
    server3.add_insecure_port("[::]:50053")  # Follower 2 on port 50053
    server3.start()
    print("gRPC server started on port 50053 (Follower 2)")

    try:
        while True:
            time.sleep(86400)  # Keep all servers running
    except KeyboardInterrupt:
        server1.stop(0)
        server2.stop(0)
        server3.stop(0)


if __name__ == "__main__":
    main()
