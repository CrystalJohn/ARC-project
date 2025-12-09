#!/bin/bash
# Validate Service - Check if backend is running correctly

set -e

echo "=== Validating Service ==="

# Wait for service to start
sleep 5

# Check if service is running
if ! systemctl is-active --quiet arc-backend; then
    echo "ERROR: arc-backend service is not running"
    systemctl status arc-backend
    exit 1
fi

# Health check
echo "Performing health check..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "$HEALTH_CHECK" != "200" ]; then
    echo "ERROR: Health check failed with status $HEALTH_CHECK"
    journalctl -u arc-backend --no-pager -n 50
    exit 1
fi

echo "Service validation passed!"
echo "Backend is running and healthy"
