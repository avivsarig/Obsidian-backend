#!/bin/bash
set -euo pipefail

# Variables (passed via templatefile)
PROJECT_NAME="${project_name}"
ENVIRONMENT="${environment}"

# Logging setup
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting bootstrap for $${PROJECT_NAME} ($${ENVIRONMENT}) at $(date)"

# System updates
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

# Install Docker (only if not present)
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker ubuntu
    systemctl enable docker
    systemctl start docker
    echo "Docker installed successfully"
fi

# Install Docker Compose v2
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..."
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$$(uname -m)" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    echo "Docker Compose installed successfully"
fi

# Install essential tools
echo "Installing system tools..."
apt-get install -y git htop unzip awscli ufw fail2ban jq curl wget

# Basic security configuration
echo "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTPS'
ufw allow 443/tcp comment 'HTTPS'

# Configure fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Setup application directory
echo "Setting up application directory..."
mkdir -p "/opt/$${PROJECT_NAME}"
chown ubuntu:ubuntu "/opt/$${PROJECT_NAME}"

# Create docker-compose directory
mkdir -p "/opt/$${PROJECT_NAME}/docker"
chown ubuntu:ubuntu "/opt/$${PROJECT_NAME}/docker"

# Configure automatic security updates only
echo "Configuring automatic updates..."
apt-get install -y unattended-upgrades
echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
echo 'Unattended-Upgrade::Remove-Unused-Dependencies "true";' >> /etc/apt/apt.conf.d/50unattended-upgrades

# Set timezone
timedatectl set-timezone UTC

# Create a simple health check endpoint for load balancer
cat > /opt/$${PROJECT_NAME}/health.html << EOF
<!DOCTYPE html>
<html>
<head><title>$${PROJECT_NAME} Health Check</title></head>
<body>
    <h1>$${PROJECT_NAME} ($${ENVIRONMENT})</h1>
    <p>Status: OK</p>
    <p>Timestamp: $$(date)</p>
</body>
</html>
EOF

# Log completion
echo "Bootstrap completed successfully for $${PROJECT_NAME} ($${ENVIRONMENT}) at $$(date)" | tee -a /var/log/bootstrap.log

# Signal completion to CloudFormation/Terraform (if using)
/opt/aws/bin/cfn-signal -e $$? --stack $${AWS_STACK_NAME:-none} --resource $${AWS_RESOURCE:-none} --region $${AWS_REGION:-eu-west-1} || true