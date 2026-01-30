# tysd-bbc-distributed-pos

## Setup

Create an virtual environment, and install dependencies.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Compile the GRPC (?)

```sh
./setup.sh
```

## Run tool

### Run all the nodes at the same time
```
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