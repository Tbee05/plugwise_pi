#!/bin/bash

# Plugwise Pi Deployment Script for Raspberry Pi
# This script sets up the Plugwise Pi project on a Raspberry Pi

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/pi/plugwise_pi"
SERVICE_DIR="/etc/systemd/system"
USER="pi"
GROUP="pi"

echo -e "${GREEN}Plugwise Pi Deployment Script${NC}"
echo "================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}"
   exit 1
fi

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}Warning: This script is designed for Raspberry Pi${NC}"
fi

# Update system packages
echo -e "${GREEN}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo -e "${GREEN}Installing required system packages...${NC}"
sudo apt install -y python3 python3-pip python3-venv sqlite3 git

# Create project directory
echo -e "${GREEN}Setting up project directory...${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Clone repository (if not already present)
if [ ! -d ".git" ]; then
    echo -e "${GREEN}Cloning repository...${NC}"
    # Replace with your actual repository URL
    # git clone https://github.com/yourusername/plugwise_pi.git .
    echo -e "${YELLOW}Please clone your repository manually or copy files to $PROJECT_DIR${NC}"
fi

# Create virtual environment
echo -e "${GREEN}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo -e "${GREEN}Creating necessary directories...${NC}"
mkdir -p data logs

# Copy configuration
echo -e "${GREEN}Setting up configuration...${NC}"
if [ ! -f "config/config.yaml" ]; then
    cp config/config.example.yaml config/config.yaml
    echo -e "${YELLOW}Please edit config/config.yaml with your device settings${NC}"
fi

# Set proper permissions
echo -e "${GREEN}Setting permissions...${NC}"
chmod +x scripts/deploy.sh
chmod 644 systemd/*.service

# Install systemd services
echo -e "${GREEN}Installing systemd services...${NC}"
sudo cp systemd/plugwise-pi.service "$SERVICE_DIR/"
sudo cp systemd/plugwise-pi-api.service "$SERVICE_DIR/"

# Reload systemd
sudo systemctl daemon-reload

# Enable services
echo -e "${GREEN}Enabling services...${NC}"
sudo systemctl enable plugwise-pi.service
sudo systemctl enable plugwise-pi-api.service

# Create logrotate configuration
echo -e "${GREEN}Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/plugwise-pi > /dev/null <<EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $GROUP
}
EOF

# Create firewall rules (optional)
echo -e "${GREEN}Setting up firewall rules...${NC}"
if command -v ufw &> /dev/null; then
    sudo ufw allow 8080/tcp  # API port
    sudo ufw allow 9090/tcp  # Prometheus metrics port
    echo -e "${GREEN}Firewall rules added${NC}"
else
    echo -e "${YELLOW}ufw not found, skipping firewall configuration${NC}"
fi

# Create startup script
echo -e "${GREEN}Creating startup script...${NC}"
cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/bin/bash
# Startup script for Plugwise Pi

cd /home/pi/plugwise_pi
source venv/bin/activate

# Start the collector in the background
python -m plugwise_pi.collector &
COLLECTOR_PID=$!

# Start the API server
python -m plugwise_pi.api &
API_PID=$!

# Wait for processes
wait $COLLECTOR_PID $API_PID
EOF

chmod +x "$PROJECT_DIR/start.sh"

# Create status script
echo -e "${GREEN}Creating status script...${NC}"
cat > "$PROJECT_DIR/status.sh" << 'EOF'
#!/bin/bash
# Status script for Plugwise Pi

echo "=== Plugwise Pi Status ==="
echo "Services:"
systemctl status plugwise-pi.service --no-pager -l
echo ""
systemctl status plugwise-pi-api.service --no-pager -l
echo ""
echo "Logs:"
tail -n 20 /home/pi/plugwise_pi/logs/plugwise.log 2>/dev/null || echo "No logs found"
EOF

chmod +x "$PROJECT_DIR/status.sh"

# Create update script
echo -e "${GREEN}Creating update script...${NC}"
cat > "$PROJECT_DIR/update.sh" << 'EOF'
#!/bin/bash
# Update script for Plugwise Pi

cd /home/pi/plugwise_pi

# Stop services
sudo systemctl stop plugwise-pi.service
sudo systemctl stop plugwise-pi-api.service

# Pull latest changes
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start services
sudo systemctl start plugwise-pi.service
sudo systemctl start plugwise-pi-api.service

echo "Update completed!"
EOF

chmod +x "$PROJECT_DIR/update.sh"

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit config/config.yaml with your Plugwise device settings"
echo "2. Start the services:"
echo "   sudo systemctl start plugwise-pi.service"
echo "   sudo systemctl start plugwise-pi-api.service"
echo "3. Check status: $PROJECT_DIR/status.sh"
echo "4. View logs: tail -f $PROJECT_DIR/logs/plugwise.log"
echo ""
echo -e "${GREEN}API will be available at: http://localhost:8080${NC}"
echo -e "${GREEN}API documentation at: http://localhost:8080/docs${NC}" 