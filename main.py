from src.pos.pos import PointOfSale


def main():
    pos1 = PointOfSale("POS1")
    pos2 = PointOfSale("POS2")
    pos3 = PointOfSale("POS3")


    pos1.add_peer(pos2, "localhost:8001")
    pos1.add_peer(pos3, "localhost:8002")

    pos1.broadcast_message("Hello from POS1")


if __name__ == "__main__":
    main()