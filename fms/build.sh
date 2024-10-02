#!/bin/bash
# Install PostgreSQL client and development headers
apt-get update && apt-get install -y libpq-dev gcc
# Install Python dependencies
pip install -r requirements.txt
