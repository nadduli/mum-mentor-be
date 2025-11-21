#!/bin/bash

# Server setup script for Mum Mentor API deployment
# This script should be run once on a fresh server
# Usage: sudo ./server-setup.sh

set -e  # Exit on error

echo "========================================="
echo "Mum Mentor API - Server Setup Script"
echo "========================================="

# Configuration
APP_DIR="/var/www/mum-mentor-be"
APP_USER="kaizen"
VENV_DIR="$APP_DIR/venv"
PYTHON_VERSION="3.12"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Update system packages
print_info "Updating system packages..."
apt-get update && apt-get upgrade -y
print_success "System packages updated"

# Add deadsnakes PPA for Python 3.11
print_info "Adding deadsnakes PPA for Python 3.11..."
apt-get install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update
print_success "deadsnakes PPA added"

# Install system dependencies
print_info "Installing system dependencies..."
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    supervisor \
    ufw \
    certbot \
    python3-certbot-nginx
print_success "System dependencies installed"

# Create application directory
print_info "Creating application directory..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"
print_success "Application directory created: $APP_DIR"

# Create Python virtual environment
print_info "Creating Python virtual environment..."
python${PYTHON_VERSION} -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
print_success "Virtual environment created"

# Prompt for repository URL
print_info "Please enter your Git repository URL:"
read -r REPO_URL

# Clone repository or use existing code
if [ -z "$(ls -A $APP_DIR)" ] || [ ! -d "$APP_DIR/.git" ]; then
    print_info "Cloning repository..."
    git clone "$REPO_URL" "$APP_DIR/temp"
    mv "$APP_DIR/temp/"* "$APP_DIR/"
    mv "$APP_DIR/temp/".* "$APP_DIR/" 2>/dev/null || true
    rm -rf "$APP_DIR/temp"
    print_success "Repository cloned"
else
    print_info "Repository already exists, pulling latest changes from origin/dev..."
    git pull origin dev
fi

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Setup PostgreSQL database
print_info "Setting up PostgreSQL database..."
print_info "Enter database name (default: mum_mentor_ai):"
read -r DB_NAME
DB_NAME=${DB_NAME:-mum_mentor_ai}

print_info "Enter database user (default: mum_mentor_user):"
read -r DB_USER
DB_USER=${DB_USER:-mum_mentor_user}

print_info "Enter database password:"
read -rs DB_PASSWORD

# Create PostgreSQL user and database
sudo -u postgres psql <<EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF
print_success "PostgreSQL database created"

# Create .env file
print_info "Creating .env file..."
cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
ENVIRONMENT=production
EOF
print_success ".env file created"

# Set correct permissions
print_info "Setting correct permissions..."
chown -R $APP_USER:$APP_USER "$APP_DIR"
chmod 600 "$APP_DIR/.env"
print_success "Permissions set"

# Setup systemd service
print_info "Setting up systemd service..."
cp "$APP_DIR/mum-mentor-api.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable mum-mentor-api
systemctl start mum-mentor-api
print_success "Systemd service configured and started"

# Setup Nginx
print_info "Setting up Nginx..."
print_info "Enter your domain name (e.g., api.example.com):"
read -r DOMAIN_NAME

cat > /etc/nginx/sites-available/mum-mentor-api <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    # Serve frontend at root
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve FastAPI docs at /docs
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Serve FastAPI API at /api
    location /api {
        proxy_pass http://127.0.0.1:8000/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/mum-mentor-api /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx
print_success "Nginx configured"

# Setup firewall
print_info "Setting up firewall..."
ufw --force enable
ufw allow 'Nginx Full'
ufw allow 'OpenSSH'
print_success "Firewall configured"

# Setup SSL with Let's Encrypt using automated script
print_info "Do you want to setup SSL certificate with Let's Encrypt? (y/n)"
read -r SETUP_SSL

if [ "$SETUP_SSL" = "y" ]; then
    print_info "Enter email for SSL certificate notifications (default: admin@$DOMAIN_NAME):"
    read -r SSL_EMAIL
    SSL_EMAIL=${SSL_EMAIL:-admin@$DOMAIN_NAME}
    
    print_info "Setting up SSL certificate using automated script..."
    chmod +x "$APP_DIR/scripts/ssl-setup.sh"
    "$APP_DIR/scripts/ssl-setup.sh" "$DOMAIN_NAME" "$SSL_EMAIL"
    print_success "SSL certificate installed and auto-renewal configured"
else
    print_info "SSL setup skipped. You can run it later with:"
    print_info "sudo $APP_DIR/scripts/ssl-setup.sh $DOMAIN_NAME your-email@domain.com"
fi

# Deactivate virtual environment
deactivate

echo ""
echo "========================================="
print_success "Server setup completed successfully!"
echo "========================================="
echo ""
print_info "Application URL: http://$DOMAIN_NAME"
print_info "API Documentation: http://$DOMAIN_NAME/api/docs"
print_info ""
print_info "Useful commands:"
echo "  - Check service status: sudo systemctl status mum-mentor-api"
echo "  - View logs: sudo journalctl -u mum-mentor-api -f"
echo "  - Restart service: sudo systemctl restart mum-mentor-api"
echo "  - Deploy updates: sudo ./deploy.sh"
