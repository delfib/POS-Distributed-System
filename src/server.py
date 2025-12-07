from fastapi import FastAPI

from src.pos.point_of_sale import PointOfSale


class Server:
    def create_app(
        self, node_id: str = "pos-1", host: str = "0.0.0.0", port: int = 8000
    ) -> FastAPI:
        global pos
        pos = PointOfSale(node_id=node_id, host=host, port=port)
        app = FastAPI(title="Distributed POS", version="0.1.0")

        @app.on_event("startup")
        async def startup_event():
            pos.start()

        @app.post("/buy/{product_id}")
        async def buy(product_id: str, quantity: int = 1):
            pos.buy(product_id, quantity)
            return {"status": "success", "product_id": product_id, "quantity": quantity}

        @app.get("/product/{product_id}")
        async def get_product(product_id: str):
            return

        # solo para nodos lideres
        @app.put("/product/{product_id}/price")
        async def update_price(product_id: str):
            return

        return app
