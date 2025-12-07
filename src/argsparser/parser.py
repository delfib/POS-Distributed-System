import argparse


class ArgsParser:
    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Distributed POS Node")
        parser.add_argument("--node-id", type=str, required=True)
        parser.add_argument("--host", type=str, default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument(
            "--peer",
            action="append",
            default=[],
            metavar="ID:HOST:PORT",
            help="Peer definition using HTTP port (example: pos2:127.0.0.1:8002)",
        )
        args = parser.parse_args()
        return args
