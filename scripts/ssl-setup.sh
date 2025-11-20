#!/bin/bash

# SSL Certificate Setup and Renewal Script
# This script automates SSL certificate installation and renewal using Let's Encrypt
# Safe to re-run - includes checks to prevent overwriting existing certificates

set -e

# Configuration
DOMAIN="${1:-}"
EMAIL="${2:-admin@example.com}"
WEBROOT_PATH="/var/www/html"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
}

# Validate domain parameter
validate_domain() {
    if [[ -z "$DOMAIN" ]]; then
        error "Usage: $0 <domain> [email]
Example: $0 api.mummentor.com admin@mummentor.com"
    fi
    
    log "Setting up SSL for domain: $DOMAIN"
    log "Contact email: $EMAIL"
}

# Install required packages
install_dependencies() {
    log "Installing required packages..."
    
    # Update package list
    apt-get update -y
    
    # Install certbot and nginx plugin
    apt-get install -y certbot python3-certbot-nginx nginx
    
    log "Dependencies installed successfully"
}

# Check if certificate already exists
check_existing_cert() {
    if [[ -d "/etc/letsencrypt/live/$DOMAIN" ]]; then
        warn "SSL certificate for $DOMAIN already exists"
        read -p "Do you want to renew it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Skipping certificate installation"
            return 1
        fi
    fi
    return 0
}

# Create nginx configuration for domain verification
create_nginx_config() {
    log "Creating nginx configuration for $DOMAIN..."
    
    # Create basic nginx config for domain verification
    cat > "$NGINX_SITES_AVAILABLE/$DOMAIN" <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root $WEBROOT_PATH;
    }
    
    # Redirect all other traffic to HTTPS (will be added after SSL setup)
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

    # Enable the site
    ln -sf "$NGINX_SITES_AVAILABLE/$DOMAIN" "$NGINX_SITES_ENABLED/"
    
    # Test nginx configuration
    nginx -t || error "Nginx configuration test failed"
    
    # Reload nginx
    systemctl reload nginx
    
    log "Nginx configuration created and enabled"
}

# Obtain SSL certificate
obtain_certificate() {
    log "Obtaining SSL certificate for $DOMAIN..."
    
    # Use webroot method for certificate generation
    certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT_PATH" \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        log "SSL certificate obtained successfully"
    else
        error "Failed to obtain SSL certificate"
    fi
}

# Update nginx configuration with SSL
configure_ssl_nginx() {
    log "Updating nginx configuration with SSL settings..."
    
    # Create SSL-enabled nginx config
    cat > "$NGINX_SITES_AVAILABLE/$DOMAIN" <<EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root $WEBROOT_PATH;
    }
    
    # Redirect to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    # Application proxy (adjust for your application)
    location / {
        proxy_pass http://127.0.0.1:8000;  # FastAPI default port
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
        proxy_redirect off;
    }
}
EOF

    # Test nginx configuration
    nginx -t || error "Nginx SSL configuration test failed"
    
    # Reload nginx
    systemctl reload nginx
    
    log "SSL configuration applied successfully"
}

# Setup automatic renewal
setup_auto_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /etc/cron.d/certbot-renewal <<EOF
# Automatic certificate renewal for Let's Encrypt
# Runs twice daily at random times to avoid rate limiting
0 */12 * * * root certbot renew --quiet --nginx --post-hook "systemctl reload nginx"
EOF

    # Test renewal process
    certbot renew --dry-run || warn "Certificate renewal test failed - check configuration"
    
    log "Automatic renewal configured"
}

# Verify SSL installation
verify_ssl() {
    log "Verifying SSL installation..."
    
    # Check if certificate files exist
    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]] && [[ -f "/etc/letsencrypt/live/$DOMAIN/privkey.pem" ]]; then
        log "Certificate files found"
        
        # Show certificate expiration
        EXPIRY=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" | cut -d= -f2)
        log "Certificate expires: $EXPIRY"
        
        # Test HTTPS connection (if curl is available)
        if command -v curl &> /dev/null; then
            if curl -s -I "https://$DOMAIN" | grep -q "HTTP/"; then
                log "HTTPS connection test: SUCCESS"
            else
                warn "HTTPS connection test failed - check firewall and DNS"
            fi
        fi
    else
        error "Certificate files not found"
    fi
}

# Main execution
main() {
    log "Starting SSL setup for Mum Mentor Backend API"
    
    check_root
    validate_domain
    
    # Only proceed with certificate installation if needed
    if check_existing_cert; then
        install_dependencies
        create_nginx_config
        obtain_certificate
        configure_ssl_nginx
    fi
    
    setup_auto_renewal
    verify_ssl
    
    log "SSL setup completed successfully!"
    log "Your API should now be accessible at: https://$DOMAIN"
    log "Certificate will auto-renew every 12 hours via cron job"
}

# Run main function
main "$@"