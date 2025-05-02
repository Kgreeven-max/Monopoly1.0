#!/bin/bash

# Move to project directory (adjust if needed)
cd "$(dirname "$0")"

# Setup environment variables
export PYTHONPATH="$(pwd):$PYTHONPATH"
export FLASK_APP=app.py
export FLASK_ENV=development
export SQLALCHEMY_DATABASE_URI="sqlite:///monopoly.db"

# Check if the database exists, if not create it
if [ ! -f "monopoly.db" ]; then
    echo "Creating new database file..."
    touch monopoly.db
fi

# Install dependencies if needed (uncomment if required)
# pip3 install -r requirements.txt

echo "Starting Monopoly backend server..."
/opt/homebrew/bin/python3 app.py 