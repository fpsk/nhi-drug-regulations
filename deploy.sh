#!/bin/bash
echo "============================================================"
echo " Taiwan NHI Drug Regulations Query Engine Deployment Script"
echo "============================================================"

# Check Python 3
if command -v python3 &>/dev/null; then
    echo "[1/3] Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "[2/3] Parsing latest regulation documents into Google OKF YAML..."
    python3 -m backend.parser
    
    echo "[3/3] Starting Production Gunicorn Web Server on port 5001..."
    echo "Desktop App: http://localhost:5001/"
    echo "Mobile App:  http://localhost:5001/mobile"
    gunicorn --bind 0.0.0.0:5001 --workers 4 --threads 2 wsgi:app
else
    echo "Error: Python3 is required."
    exit 1
fi
