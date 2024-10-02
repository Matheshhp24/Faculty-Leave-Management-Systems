#!/bin/bash

echo "Running build.sh: Updating apt and installing PostgreSQL client and development headers"
apt-get update && apt-get install -y libpq-dev gcc || { echo "Failed to install libpq-dev or gcc"; exit 1; }

echo "Running build.sh: Installing Python dependencies"
pip install -r fms/requirements.txt || { echo "Failed to install Python dependencies"; exit 1; }

echo "Build.sh executed successfully!"
