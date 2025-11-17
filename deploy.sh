#!/bin/bash

# Deployment script for Mum Mentor API on bare server
# Usage: ./deploy.sh

set -e  # Exit on error

echo "========================================="
echo "Mum Mentor API Deployment Script"
echo "========================================="

# Configuration
APP_DIR="/var/www/mum-mentor-be"
APP_USER="www-data"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="mum-mentor-api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_info "Starting deployment process..."

# Navigate to application directory
cd "$APP_DIR" || {
    print_error "Application directory not found: $APP_DIR"
    exit 1
}

# Pull latest changes from git
print_info "Pulling latest changes from git (origin/dev)..."
git pull origin dev || {
    print_error "Failed to pull latest changes"
    exit 1
}
print_success "Code updated successfully"

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate" || {
    print_error "Failed to activate virtual environment"
    exit 1
}

# Install/update dependencies
print_info "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt || {
    print_error "Failed to install dependencies"
    exit 1
}
print_success "Dependencies installed successfully"

# Run database migrations (if Alembic is configured)
if [ -d "alembic" ]; then
    print_info "Running database migrations..."
    alembic upgrade head || {
        print_error "Database migration failed"
        exit 1
    }
    print_success "Database migrations completed"
fi

# Set correct permissions
print_info "Setting correct permissions..."
chown -R $APP_USER:$APP_USER "$APP_DIR"
print_success "Permissions set successfully"

# Restart the service
print_info "Restarting $SERVICE_NAME service..."
systemctl restart "$SERVICE_NAME" || {
    print_error "Failed to restart service"
    exit 1
}
print_success "Service restarted successfully"

# Check service status
print_info "Checking service status..."
sleep 2
if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_success "Service is running"
else
    print_error "Service is not running!"
    systemctl status "$SERVICE_NAME"
    exit 1
fi

echo ""
echo "========================================="
print_success "Deployment completed successfully!"
echo "========================================="
echo ""
print_info "Service status:"
systemctl status "$SERVICE_NAME" --no-pager -l

# Deactivate virtual environment
deactivate
