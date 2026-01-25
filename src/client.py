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
    
def products_list():

    products = []

    with open(db_path) as f:
        data = json.load(f)

        # print(type(data))
        for item in data:
            product = (data[item]["id"], data[item]["name"])
            products.append(product)

    products.sort()

    return products
    
def operation(products, stub):
    
    while True:
        print("\n" + "=" * 60)
        
        print("PRODUCTS\n")
        for item in products:
            print(item[0],"- "+item[1])
        
        print("\n"+"OPERATIONS")
        print("1 - GET")
        print("2 - BUY")
        print("3 - UPDATE\n")

        selected_operation = input("$ ")

        if selected_operation == '1' :
            selected_product_id = int(input("Product ID: "))
            request = GetProductPriceRequest(product_id=selected_product_id) 
            response = stub.GetProductPrice(request)
            # TODO: cambiar print
            print(f"\nResultado: ${response.price}")
            
        elif selected_operation == '2':
            
            selected_product_id = int(input("Product ID to buy: "))
            quantity_product = int(input("Quantity: "))
            request = BuyProductRequest(product_id=selected_product_id, quantity=quantity_product)
            response = stub.BuyProduct(request)
            # TODO: cambiar print
            print(f"Compra realizada: {response.success}")

        elif selected_operation == '3':
            selected_product_id = int(input("Product ID: "))
            new_price = float(input("New Price: "))
            request = UpdateProductPriceRequest(product_id=selected_product_id, new_price=new_price)
            response = stub.UpdateProductPrice(request)
            # TODO: cambiar print
            print("Precio actualizado correctamente.")
            
        else:
            # TODO: cambiar print
            break
       
        print("=" * 60)


def run():
    try:

        stub = None
        while stub is None:
            stub = connect() # Recibimos el stub aquí

        products = products_list()
        
        operation(products, stub)
       
    except grpc.RpcError as e:
        print(f"\nError: {e}")
        print("Make sure all servers are running!")


if __name__ == "__main__":
    run()
