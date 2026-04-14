#!/usr/bin/env bash

set -e  # Exit on error

VENV_DIR=".venv"
PYTHON="python3"
SCRIPT="run_pipeline.py"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run your script with all passed arguments
echo "Running script..."
python "$SCRIPT" "$@"