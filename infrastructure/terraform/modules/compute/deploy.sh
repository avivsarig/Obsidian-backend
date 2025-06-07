#!/bin/bash
# All variables come from /opt/deployment/config.env
set -euo pipefail

# Source configuration variables
# shellcheck source=/dev/null
source /opt/deployment/config.env

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a /var/log/deployment.log
}

log "Starting deployment for $PROJECT_NAME in $ENVIRONMENT environment"
log "Backend: $BACKEND_REPO_URL ($BACKEND_BRANCH)"
log "Vault: $VAULT_REPO_URL ($VAULT_BRANCH)"

# Clone backend repository
log "Cloning backend repository..."
if [ -d "/opt/backend/.git" ]; then
    log "Backend directory exists, pulling latest changes"
    cd /opt/backend
    git fetch origin
    git checkout "$BACKEND_BRANCH"
    git pull origin "$BACKEND_BRANCH"
else
    log "Cloning backend from $BACKEND_REPO_URL branch $BACKEND_BRANCH"
    git clone -b "$BACKEND_BRANCH" "$BACKEND_REPO_URL" /opt/backend
fi

chown -R ubuntu:ubuntu /opt/backend

# Clone vault repository
log "Cloning vault repository..."
if [ -d "/opt/vault/.git" ]; then
    log "Vault directory exists, pulling latest changes"
    cd /opt/vault
    git fetch origin
    git checkout "$VAULT_BRANCH"
    git pull origin "$VAULT_BRANCH"
else
    log "Cloning vault from $VAULT_REPO_URL branch $VAULT_BRANCH"
    git clone -b "$VAULT_BRANCH" "$VAULT_REPO_URL" /opt/vault
fi

chown -R ubuntu:ubuntu /opt/vault

# Set up application environment file
log "Creating application environment configuration..."
cat > /opt/backend/.env << EOF
ENVIRONMENT=$ENVIRONMENT
VAULT_PATH=/opt/vault
GIT_REPO_URL=$VAULT_REPO_URL
LOG_LEVEL=$([ "$ENVIRONMENT" = "production" ] && echo "WARNING" || echo "DEBUG")
EOF

# Set up auto-update for development environment
if [ "$AUTO_UPDATE" = "true" ]; then
    log "Setting up auto-update cron jobs for development"
    cat > /etc/cron.d/auto-update << EOF
# Auto-update backend and vault every 10 minutes in dev
*/10 * * * * ubuntu cd /opt/backend && git pull origin $BACKEND_BRANCH && docker-compose restart 2>&1 | logger -t auto-update-backend
*/10 * * * * ubuntu cd /opt/vault && git pull origin $VAULT_BRANCH 2>&1 | logger -t auto-update-vault
EOF
    log "Auto-update cron jobs configured"
else
    log "Auto-update disabled for $ENVIRONMENT environment"
fi

# Start the application
log "Starting application with Docker Compose..."
cd /opt/backend

# Check if the compose file exists
COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    log "Warning: $COMPOSE_FILE not found, falling back to docker-compose.yml"
    COMPOSE_FILE="docker-compose.yml"
fi

if [ -f "$COMPOSE_FILE" ]; then
    sudo -u ubuntu docker-compose -f "$COMPOSE_FILE" up -d
    log "Application started successfully"
else
    log "Error: No suitable docker-compose file found"
    exit 1
fi

# Wait for application to be ready
log "Waiting for application to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
        log "Application is responding to health checks"
        break
    fi
    if [ "$i" -eq 30 ]; then
        log "Warning: Application not responding after 30 attempts"
    fi
    sleep 2
done

log "Deployment completed successfully"
log "Application logs can be viewed with: docker-compose logs -f"
log "Health check: curl http://localhost:8000/api/v1/health"
