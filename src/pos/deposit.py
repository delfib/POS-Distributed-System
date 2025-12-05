import threading

class Product:
    def __init__(self, id: int, name: str, price: float):
        self.id = id
        self.name = name
        self.price = price
        self.quantity = 0

db = {
    1: Product(1, "Apple", 0.5),
    2: Product(2, "Banana", 0.3),
    3: Product(3, "Orange", 0.7)
}

class Deposit:
    def __init__(self):
        self.db : dict[int, Product] = db
        self.lock = threading.Lock()

    def sell_product(self, product_id: int, quantity: int) -> bool:
        with self.lock:
            if product_id in self.db and self.db[product_id].quantity >= quantity:
                self.db[product_id].quantity -= quantity
                return True
            return False

    def change_price(self, product_id: int, price: float) -> None:
        with self.lock:
            if product.id in self.db:
                self.db[product.id].price = price