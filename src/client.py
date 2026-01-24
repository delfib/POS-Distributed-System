import grpc
import json

import proto.pos_service_pb2_grpc as pos_service_pb2_grpc
from proto.pos_service_pb2 import (
    BuyProductRequest,
    GetProductPriceRequest,
    UpdateProductPriceRequest,
)

db_path = ''

def connect():
    
    global db_path

    with open("src/config.json") as f:
        config = json.load(f)
        nodes = config["nodes"]

        for n in nodes:
            print("node " + str(n["id"]) +" ("+ n["role"] + ")")

        nodo_select = int(input("Select a node:"))
        for n in nodes:
            if nodo_select == n["id"]:
                print(n)
                db_path = n["db"]
                channel = grpc.insecure_channel(f"{n["host"]}:{n["port"]}")
                return pos_service_pb2_grpc.POSStub(channel) # Retornamos el objeto
    return None
    
def product_list():

    print("\n" + "=" * 60)
    print("PRODUCTS\n")

    with open(db_path) as f:
        data = json.load(f)
        #print(data.values)
        #print(type(data))
        for item in data:
            print("- " + data[item]["name"])

    print("=" * 60)

    

def run():
    try:

        stub = None
        while stub is None:
            stub = connect() # Recibimos el stub aquí

        product_list()

        request = GetProductPriceRequest(product_id=1)
        response = stub.GetProductPrice(request)
        print(f"${response.price}")

            
        print("\n" + "=" * 60)
        
        print("=" * 60)

    except grpc.RpcError as e:
        print(f"\nError: {e}")
        print("Make sure all servers are running!")


if __name__ == "__main__":
    run()
