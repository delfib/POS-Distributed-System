from src.pos.client import Client
from src.pos.deposit import Deposit, Product
from src.pos.pos import PointOfSale, Role


def build_peer_topology():
    pos1_deposit = Deposit(
        {
            1: Product(1, "Apple", 0.55, 0),
            2: Product(2, "Banana", 0.3, 10),
            3: Product(3, "Orange", 0.7, 8),
        }
    )
    pos1 = PointOfSale("POS1", deposit=pos1_deposit)

    # POS2 has no local apples to start with.
    pos2_deposit = Deposit(
        {
            1: Product(1, "Apple", 0.5, 0),
            2: Product(2, "Banana", 0.3, 10),
            3: Product(3, "Orange", 0.7, 8),
        }
    )
    pos2 = PointOfSale("POS2", deposit=pos2_deposit)
    pos3 = PointOfSale("POS3")

    pos1.add_peer(pos2, "localhost:8001")
    pos1.add_peer(pos3, "localhost:8002")
    pos2.add_peer(pos1, "localhost:8000")
    pos2.add_peer(pos3, "localhost:8002")
    pos3.add_peer(pos1, "localhost:8000")
    pos3.add_peer(pos2, "localhost:8001")
    return pos1, pos2, pos3


def main():
    pos1, pos2, pos3 = build_peer_topology()
    pos1.set_role(Role.LEADER)

    client = Client(pos2)

    product = client.get_item(1)
    print(f"[Before leader update] Client sees {product.name} at ${product.price}")

    pos1.update_price(1, 0.55)
    product = client.get_item(1)
    print(f"[After leader update] Client sees {product.name} at ${product.price}")

    # This sale will be fulfilled by POS3 because POS2 has 0 apples.
    client.buy_item(product_id=1, quantity=4)

    pos1.broadcast_message("Inventory updated across the network.")


if __name__ == "__main__":
    main()
