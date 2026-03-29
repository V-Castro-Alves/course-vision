#!/bin/bash

# Go to project root (assumes this script is located at project root)
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Install dependencies (optional; uncomment if you want automatic install)
# pip install -r requirements.txt

# Run all tests with unittest
venv/bin/python -m unittest discover -s tests -p "test_*.py" --verbose
