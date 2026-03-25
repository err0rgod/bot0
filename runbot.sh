#!/bin/bash

VENV_DIR="venv"

# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python -m venv $VENV_DIR
fi

# Activate the virtual environment
echo "Activating virtual environment..."
if [ -f "$VENV_DIR/Scripts/activate" ]; then
    # Windows (Git Bash)
    source $VENV_DIR/Scripts/activate
elif [ -f "$VENV_DIR/bin/activate" ]; then
    # Linux / macOS / WSL
    source $VENV_DIR/bin/activate
else
    echo "Error: Could not find the activation script in $VENV_DIR."
    exit 1
fi

echo "Installing/updating requirements..."
pip install -r requirements.txt

echo "Starting the bot..."
python v2.py
