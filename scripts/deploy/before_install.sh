#!/bin/bash
# Before Install - Stop existing service and clean up

set -e

echo "=== Before Install ==="

# Stop existing service if running
if systemctl is-active --quiet arc-backend; then
    echo "Stopping existing arc-backend service..."
    systemctl stop arc-backend
fi

# Clean up old deployment
if [ -d "/opt/arc-chatbot/backend" ]; then
    echo "Removing old deployment..."
    rm -rf /opt/arc-chatbot/backend
fi

# Create directory structure
mkdir -p /opt/arc-chatbot/backend
mkdir -p /var/log/arc-chatbot

echo "Before install completed"
