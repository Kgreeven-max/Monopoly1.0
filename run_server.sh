#!/bin/bash

# Add the project root to PYTHONPATH
export PYTHONPATH=$(pwd):$PYTHONPATH

# Run the Flask app
/opt/homebrew/bin/python3 app.py 