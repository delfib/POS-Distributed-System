import uvicorn

from src.argsparser.parser import ArgsParser
from src.server import Server


def main():
    args = ArgsParser.build_parser()
    server = Server()
    app = server.create_app(node_id=args.node_id, host=args.host, port=args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
