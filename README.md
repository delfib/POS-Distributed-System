# Setup

## Create a virtual environment, and install dependencies.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Compile the gRPC .proto definition and generate Python stubs. Required for client-server RPC communication

```sh
./setup.sh
```

## Run tool

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

If you want to run and see the three nodes (`pos1`, `pos2`, `pos3`), use Docker with:

```sh
docker compose up --build
```
