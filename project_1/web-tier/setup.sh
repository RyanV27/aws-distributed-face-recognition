#!/bin/bash
# web_tier_setup.sh
# This script sets up a Python virtual environment and installs required packages

set -e  # Exit immediately if a command exits with a non-zero status

echo "Updating package lists..."
sudo apt update -y

echo "Installing Python3 pip and venv..."
sudo apt install -y python3-pip python3-venv

echo "Creating virtual environment 'cloud_venv'..."
python3 -m venv cloud_venv

echo "Activating virtual environment..."
source cloud_venv/bin/activate

echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install boto3 flask gunicorn gevent

echo "Setup complete! To activate the environment later, run:"
echo "source cloud_venv/bin/activate"