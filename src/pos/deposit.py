import threading

class Product:
    def __init__(self, id: int, name: str, price: float):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = 0

class Deposit:
    def __init__(self):
        self.db : dict[int, Product] = {}
        self.lock = threading.Lock()

    def sell_product(self, product_id: int, quantity: int) -> bool:
        with self.lock:
            if product_id in self.db and self.db[product_id].quantity >= quantity:
                self.db[product_id].quantity -= quantity
                return True
            return False

    def add_product(self, product: Product, quantity: int) -> None:
        with self.lock:
            if product.id in self.db:
                self.db[product.id].quantity += quantity
            else:
                product.quantity = quantity
                self.db[product.id] = product
    
    def change_price(self, product: Product, price: float) -> None:
        with self.lock:
            if product.id in self.db:
                self.db[product.id].price = price