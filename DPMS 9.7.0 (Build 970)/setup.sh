#!/bin/bash
set -e

echo "Installing DPMS..."

python3 -m pip install --upgrade pip
python3 -m pip install -e .

echo "Done. You can now run: dpms"
