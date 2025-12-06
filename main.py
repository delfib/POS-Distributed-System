from src.argsparser.parser import ArgsParser
from src.pos.pos import PointOfSale


def main():
    args = ArgsParser.build_parser()
    pos = PointOfSale(node_id=args.node_id, host=args.host, port=args.port)
    pos.start()


if __name__ == "__main__":
    main()
