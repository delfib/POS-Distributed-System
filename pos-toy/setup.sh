#!/bin/bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd src
python3 -m grpc_tools.protoc -I. --python_out=./ --grpc_python_out=./ proto/pos_service.proto
cd ..
