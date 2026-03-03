# Distributed Point of Sale System
A distributed Point of Sale (POS) system composed of multiple nodes, each representing an independent store with its own local database and inventory.
TThe system simulates a real-world distributed retail environment in which:
* A designated leader node is responsible for updating product prices
* Price updates are propagated consistently across all nodes
* Stores can sell products not available locally by sourcing them from other nodes
* Clients can connect to any node to query prices or purchase products

The primary goal of this project is to explore and implement distributed systems concepts, including leader election, replication, consistency, and fault tolerance.

## Setup

### Create a virtual environment, and install dependencies.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Compile the gRPC .proto definition and generate Python stubs. Required for client-server RPC communication

```sh
./setup.sh
```

## Run the System

### Run all the nodes at the same time

```sh
./start_pos.sh
```

### Run each node individually

```py
python3 src/server.py --id node-number
```

### Run the client

```py
python3 src/client.py
```

## Docker

To run the three nodes (`pos1`, `pos2`, `pos3`) using Docker:

```sh
docker compose up --build
```
