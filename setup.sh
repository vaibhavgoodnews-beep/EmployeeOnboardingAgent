#!/bin/bash

# Quick Start Script for Employee Onboarding Agent (Unix/Linux/Mac)

echo ""
echo "======================================"
echo "Employee Onboarding Agent - Setup"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

echo "[1/4] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

echo ""
echo "[2/4] Activating virtual environment..."
source venv/bin/activate

echo ""
echo "[3/4] Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "[4/4] Setting up secrets..."
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo ""
    echo "Please create .streamlit/secrets.toml with your Google API key:"
    echo ""
    echo "Copy the template from .streamlit/secrets.toml.template"
    echo "And add your actual API key"
else
    echo "Secrets file already exists"
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the app, run:"
echo "   streamlit run app.py"
echo ""
