#!/bin/bash

echo "Running build.sh: Installing PostgreSQL client and development headers"
apt-get update && apt-get install -y libpq-dev gcc

echo "Running build.sh: Installing Python dependencies"
pip install -r requirements.txt
