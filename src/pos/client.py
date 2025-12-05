from src.pos.deposit import Product
from src.pos.pos import PointOfSale, DOWN

class Client:
    def __init__(self):
        pass  
        
    def buy_item(self, product: Product, pos: PointOfSale):
        """Buy a specified quantity of a product."""
        pass

    def get_item(self, product: Product, pos: PointOfSale):
        """Retrieve a product from the Point of Sale system."""
        pass
