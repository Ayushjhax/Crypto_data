#!/bin/bash
# Simple script to run the data collection pipeline
# Usage: ./run.sh or bash run.sh

cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py

