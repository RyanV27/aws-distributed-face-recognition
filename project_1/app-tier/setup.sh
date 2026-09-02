#!/bin/bash
# ==========================================
# Setup Python virtual environment and install dependencies
# ==========================================

set -e  # Exit immediately if a command exits with a non-zero status

echo "Updating system packages..."
sudo apt update -y

echo "Installing Python and required packages..."
sudo apt install -y python3-pip python3-venv

echo "Creating Python virtual environment..."
python3 -m venv cloud_venv

echo "Activating virtual environment..."
source cloud_venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing PyTorch (CPU version) and other dependencies..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install boto3 requests

echo "Setup complete! Virtual environment 'cloud_venv' is ready in $(pwd)"