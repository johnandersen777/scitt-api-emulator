#!/bin/bash

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install wheel
pip install -e .

# Install test dependencies
pip install pytest docker

# Build Docker image
docker build -t acdc_fastapi .

echo "Setup complete. You can now run tests using 'pytest'."
