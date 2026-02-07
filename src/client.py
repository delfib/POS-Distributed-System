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

    config_file = os.getenv("CONFIG_FILE", "src/config.json")
    with open(config_file) as f:
        config = json.load(f)
        nodes = config["nodes"]

        for n in nodes:
            print("node " + str(n["id"]))

        nodo_select = int(input("Select a node:"))
        for n in nodes:
            if nodo_select == n["id"]:
                db_path = n["db"]
                channel = grpc.insecure_channel(f"{n['host']}:{n['port']}")
                return pos_service_pb2_grpc.POSStub(channel) 
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

        print("PRODUCTS\n")
        for item in products:
            print(item[0], "- " + item[1])

        print("\n" + "OPERATIONS")
        print("1 - SHOW PRODUCT PRICE")
        print("2 - BUY PRODUCT")
        print("3 - UPDATE PRODUCT\n")

        selected_operation = input("$ ")

        match selected_operation:
            case "1":
                selected_product_id = int(input("Product ID: "))

                if selected_product_id not in products_ids:
                    raise ValueError(f"Unknown product id {selected_product_id}")

                request = GetProductPriceRequest(product_id=selected_product_id)
                response = stub.GetProductPrice(request)

                print(f"\nPrice: ${response.price}")

            case "2":
                selected_product_id = int(input("Product ID to buy: "))

                if selected_product_id not in products_ids:
                    raise ValueError(f"Unknown product id {selected_product_id}")

                quantity_product = int(input("Quantity: "))
                request = BuyProductRequest(
                    product_id=selected_product_id, quantity=quantity_product
                )
                response = stub.BuyProduct(request)

                if response.success:
                    print(f"Purchase made: {response.success}")
                else:
                    raise ValueError("Failed operation")

            case "3":
                selected_product_id = int(input("Product ID: "))

                if selected_product_id not in products_ids:
                    raise ValueError(f"Unknown product id {selected_product_id}")

                new_price = float(input("New Price: "))
                request = UpdateProductPriceRequest(
                    product_id=selected_product_id, new_price=new_price
                )
                response = stub.UpdateProductPrice(request)

                if response.success:
                    print("Price updated.")
                else:
                    raise ValueError("Failed operation")

            case _:
                raise ValueError(f"Unknown operation {selected_operation}")

        time.sleep(1.5)

        print("=" * 60)


def reload_all_databases():
    """Reload database from disk on all nodes."""
    print("\n" + "=" * 60)
    print("Reloading Databases on All Nodes")
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
            print(f"   {node_name}: {response.message}")

            channel.close()
        except grpc.RpcError as e:
            print(f"   {node_name}: Failed to reload - {e.code().name}")


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