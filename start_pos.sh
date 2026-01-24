#!/bin/bash

git restore src/db/*

gnome-terminal -- bash -c "source .venv/bin/activate && python3 src/server.py --id 1; exec bash"
gnome-terminal -- bash -c "source .venv/bin/activate && python3 src/server.py --id 2; exec bash"
gnome-terminal -- bash -c "source .venv/bin/activate && python3 src/server.py --id 3; exec bash"
