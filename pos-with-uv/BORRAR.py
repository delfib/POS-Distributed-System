class Node:
    def __init__(self, node_id, port, all_nodes):
        # Crear todas las clases
        self.db = Database(node_id)
        self.network = NetworkManager(node_id, port, all_nodes)
        self.leader_election = LeaderElection(node_id, all_nodes, self.network)
        self.health = HealthMonitor(node_id, self.network, self.leader_election)
        self.transaction_mgr = TransactionManager(node_id, self.network, self.db)

        # Decirle a Network que cuando llegue un mensaje, llame a handle_message
        self.network.set_message_handler(self.handle_message)

    def start(self):
        # Iniciar todos los componentes
        self.network.start_server()  # Escuchar mensajes
        self.health.start()  # Iniciar heartbeats
        self.leader_election.start_election()  # Elegir líder

    def handle_message(self, message):
        """Cuando llega un mensaje, Node decide qué hacer"""

        if message["type"] == "PING":
            # Delegar a HealthMonitor
            return self.health.handle_ping(message["from"], message["timestamp"])

        elif message["type"] == "ELECTION":
            # Delegar a LeaderElection
            return self.leader_election.handle_election_message(message["from"])

        elif message["type"] == "BUY_PRODUCT":
            # Delegar a TransactionManager
            return self.transaction_mgr.initiate_sale(
                message["product_id"], message["quantity"]
            )

        elif message["type"] == "UPDATE_PRICE":
            # Node maneja esto directamente
            return self.update_price(message["product_id"], message["price"])
