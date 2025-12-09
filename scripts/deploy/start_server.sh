#!/bin/bash
# Start Server - Launch FastAPI backend

set -e

echo "=== Starting Server ==="

# Create systemd service if not exists
cat > /etc/systemd/system/arc-backend.service << 'EOF'
[Unit]
Description=ARC Chatbot Backend API
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/opt/arc-chatbot/backend
Environment="PATH=/opt/arc-chatbot/backend/venv/bin"
EnvironmentFile=/opt/arc-chatbot/backend/.env
ExecStart=/opt/arc-chatbot/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload and start service
systemctl daemon-reload
systemctl enable arc-backend
systemctl start arc-backend

echo "Server started successfully"
