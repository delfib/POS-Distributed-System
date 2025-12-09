### Set up the Virtual Environment

In your project directory, create a virtual environment:

```bash
python3 -m venv venv
```

### Activate the virtual environment:
```bash
source venv/bin/activate
```

### Install Required Dependencies

```bash
pip install grpcio grpcio-tools
```

### Generate gRPC Code from .proto File (if not already generated)
```bash
~/UNRC/redes/pos-toy/src$ python3 -m grpc_tools.protoc -I. --python_out=./ --grpc_python_out=./ proto/pos_service.proto 
```

### Run the servers in Terminal 1
```bash
python3 pos.py
```


### Run the client in Terminal 2
```bash
python3 client.py
```