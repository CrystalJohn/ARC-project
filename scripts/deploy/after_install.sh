#!/bin/bash
# After Install - Install dependencies and configure

set -e

echo "=== After Install ==="

cd /opt/arc-chatbot/backend

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set permissions
chown -R ec2-user:ec2-user /opt/arc-chatbot
chmod -R 755 /opt/arc-chatbot

# Copy environment file if exists
if [ -f "/home/ec2-user/.env.backend" ]; then
    cp /home/ec2-user/.env.backend /opt/arc-chatbot/backend/.env
fi

echo "After install completed"
