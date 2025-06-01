#!/bin/bash
# shellcheck disable=SC2154
set -euo pipefail

# Template variables from OpenTofu - these get substituted
export PROJECT_NAME="${project_name}"
export ENVIRONMENT="${environment}"

# System updates
apt-get update
apt-get install -y nginx docker.io docker-compose git awscli

# Create application directory
mkdir -p "/opt/$${PROJECT_NAME}"

# Docker setup
systemctl enable docker
systemctl start docker
usermod -a -G docker ubuntu

# Health check endpoint
cat > "/opt/$${PROJECT_NAME}/health.html" << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Health Check</title></head>
<body><h1>Service is running</h1></body>
</html>
EOF
