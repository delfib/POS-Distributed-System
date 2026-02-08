import json
import os
import time

import grpc

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from proto.pos_service_pb2 import (
    BuyProductRequest,
    GetProductPriceRequest,
    ReloadDatabaseRequest,
    UpdateProductPriceRequest,
)

db_path = ""


def connect():
    """
    Connects the client to a selected POS node.

    - Loads node configuration from config.json
    - Prompts the user to select a node
    - Creates a gRPC channel to that node
    - Returns a POSStub for RPC calls
    """
    global db_path

    print("\n" + "=" * 60)
    print("POS CLIENT — NODE CONNECTION")
    print("=" * 60)

    config_file = os.getenv("CONFIG_FILE", "src/config.json")
    with open(config_file) as f:
        config = json.load(f)
        nodes = config["nodes"]

        print("\nAvailable POS nodes:")
        for n in nodes:
            print("node " + str(n["id"]))

        try:
            nodo_select = int(input("\nSelect a node to connect to: "))
        except ValueError:
            print("Invalid input. Please enter a numeric node ID.")
            return None

        for n in nodes:
            if nodo_select == n["id"]:
                db_path = n["db"]
                channel = grpc.insecure_channel(f"{n['host']}:{n['port']}")
                print(f"\nSuccessfully connected to node {n['id']}.")
                return pos_service_pb2_grpc.POSStub(channel)

    print("Selected node not found. Please select a valid node id.")
    return None


def products_list():
    """Loads and returns the list of products from the local JSON database file."""
    products = []

    with open(db_path) as f:
        data = json.load(f)

        for item in data:
            product = (data[item]["id"], data[item]["name"])
            products.append(product)

    products.sort()

    return products


def manage_product_operations(products, stub):
    """
    Interactive client menu for product operations.
    Allows the user to:
    - Query product price
    - Buy products
    - Update product price 
    """
    products_ids = []

    for id in products:
        products_ids.append(id[0])

    while True:
        print("\n" + "=" * 60)
        print("PRODUCT CATALOG")
        print("=" * 60)

        for item in products:
            print(item[0], "- " + item[1])

        print("\nAVAILABLE OPERATIONS")
        print("  1 - Show product price")
        print("  2 - Buy product")
        print("  3 - Update product price")
        print("  0 - Exit")

        selected_operation = input("\nSelect an operation: ").strip()

        match selected_operation:
            case "1":
                selected_product_id = int(input("Enter product ID: "))

                if selected_product_id not in products_ids:
                    print("Unknown product ID. Please retry.")
                    continue

                request = GetProductPriceRequest(product_id=selected_product_id)
                response = stub.GetProductPrice(request)

                print(f"\nProduct price: ${response.price}")

            case "2":
                selected_product_id = int(input("Enter product ID to buy: "))

                if selected_product_id not in products_ids:
                    print("Unknown product ID. Please retry.")
                    continue

                quantity_product = int(input("Enter quantity: "))
                request = BuyProductRequest(
                    product_id=selected_product_id, quantity=quantity_product
                )
                response = stub.BuyProduct(request)

                if response.success:
                    print(f"Purchase successful. Units sold: {response.quantity_sold}")
                else:
                    print(f"Purchase failed: {response.message}")

            case "3":
                selected_product_id = int(input("Enter product ID: "))

                if selected_product_id not in products_ids:
                    print("Unknown product ID. Please retry.")
                    continue

                new_price = float(input("Enter new price: "))
                request = UpdateProductPriceRequest(
                    product_id=selected_product_id, new_price=new_price
                )
                response = stub.UpdateProductPrice(request)

                if response.success:
                    print("Product price updated successfully.")
                else:
                    print(f"Price update failed: {response.message}")

            case "0":
                print("\nExiting POS client. Goodbye!")
                return

            case _:
                print("Invalid option. Please select a valid operation.")

        time.sleep(1.2)


def reload_all_databases():
    """Reload database from disk on all nodes."""
    print("\n" + "=" * 60)
    print("RELOADING DATABASES ON ALL NODES")
    print("=" * 60)

    nodes = [
        ("POS1", "localhost", 50051),
        ("POS2", "localhost", 50052),
        ("POS3", "localhost", 50053),
    ]

    for node_name, host, port in nodes:
        try:
            channel = grpc.insecure_channel(f"{host}:{port}")
            stub = pos_service_pb2_grpc.POSStub(channel)

            request = ReloadDatabaseRequest()
            response = stub.ReloadDatabase(request)
            print(f"{node_name}: {response.message}")

            channel.close()
        except grpc.RpcError as e:
            print(f"{node_name}: Failed to reload ({e.code().name})")


def run():
    try:
        stub = None
        while stub is None:
            stub = connect()

        products = products_list()

        manage_product_operations(products, stub)

    except grpc.RpcError as e:
        print(f"\nError: {e}")
        print("Make sure all servers are running!")


if __name__ == "__main__":
    run()