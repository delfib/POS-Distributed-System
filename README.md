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

```py
python3 src/server.py
```

```py
python3 src/client.py
```