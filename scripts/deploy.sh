#!/bin/bash
set -e

echo "=== SchoolShare DSS Deployment ==="
cd /opt/dss-app

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Stop and remove old container
echo "Stopping old container..."
docker stop dss-app 2>/dev/null || true
docker rm dss-app 2>/dev/null || true

# Build new image
echo "Building Docker image..."
docker build -t dss-app .

# Run new container
echo "Starting new container..."
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data:ro \
  --name dss-app \
  --restart unless-stopped \
  dss-app

# Wait for startup
echo "Waiting for app to start..."
sleep 10

# Health check
echo "Running health check..."
if curl -s --fail http://localhost:8501/_stcore/health > /dev/null; then
  echo "✓ Health check passed"
else
  echo "✗ Health check failed"
  docker logs dss-app --tail 20
  exit 1
fi

# Verify container status
echo ""
echo "=== Container Status ==="
docker ps | grep dss-app

echo ""
echo "=== Deployment Complete ==="
echo "App available at: http://schoolsharedss.org"
echo "Direct access: http://164.92.92.181:8501"
