#!/bin/bash

git restore src/db/*

gnome-terminal -- bash -c "source .venv/bin/activate && python3 src/server.py --id POS1; exec bash"
gnome-terminal -- bash -c "source .venv/bin/activate && python3 src/server.py --id POS2; exec bash"
gnome-terminal -- bash -c "source .venv/bin/activate && python3 src/server.py --id POS3; exec bash"
