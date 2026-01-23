import grpc

from proto import pos_service_pb2_grpc


class RPCCaller:
    @staticmethod
    def execute_rpc_call(
        peer_host: str, peer_port: int, method_name: str, request_obj, timeout=5.0
    ):
        """Contact a peer and execute an RPC call. Returns (success: bool, response: Any)"""
        try:
            channel = grpc.insecure_channel(f"{peer_host}:{peer_port}")
            stub = pos_service_pb2_grpc.POSStub(channel)

            method = getattr(stub, method_name)
            response = method(request_obj, timeout=timeout)

            channel.close()
            return True, response
        except grpc.RpcError as e:
            print(f"Failed to contact {peer_host}:{peer_port}: {e}")
            return False, None
