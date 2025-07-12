#!/bin/bash

# Plugwise Data Collector Installation Script
# For Raspberry Pi deployment

set -e

echo "🔌 Plugwise Data Collector Installation"
echo "========================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Create application directory
APP_DIR="/home/pi/plugwise_pi"
echo "📁 Creating application directory: $APP_DIR"
mkdir -p "$APP_DIR"

# Copy files to application directory
echo "📋 Copying application files..."
cp plugwise_collector.py "$APP_DIR/"
cp config.json "$APP_DIR/"
cp requirements.txt "$APP_DIR/"
cp README.md "$APP_DIR/"

# Create data and logs directories
mkdir -p "$APP_DIR/data"
mkdir -p "$APP_DIR/logs"

# Set up Python virtual environment
echo "🔧 Setting up Python virtual environment..."
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/plugwise-collector.service > /dev/null <<EOF
[Unit]
Description=Plugwise Data Collector
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/plugwise_collector.py --continuous --interval 60 --output $APP_DIR/data
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable plugwise-collector
sudo systemctl start plugwise-collector

# Check service status
echo "📊 Service status:"
sudo systemctl status plugwise-collector --no-pager

# Create log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/plugwise-collector > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 pi pi
}
EOF

# Set permissions
echo "🔐 Setting permissions..."
sudo chown -R pi:pi "$APP_DIR"
chmod +x "$APP_DIR/plugwise_collector.py"

# Create test script
echo "🧪 Creating test script..."
tee "$APP_DIR/test_collector.py" > /dev/null <<EOF
#!/usr/bin/env python3
"""Test script for Plugwise collector"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plugwise_collector import PlugwiseCollector

if __name__ == "__main__":
    print("🧪 Testing Plugwise Collector...")
    collector = PlugwiseCollector()
    result = collector.run_single_collection("data")
    
    if result:
        print("✅ Test successful!")
    else:
        print("❌ Test failed!")
EOF

chmod +x "$APP_DIR/test_collector.py"

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit configuration: nano $APP_DIR/config.json"
echo "2. Test the collector: python3 $APP_DIR/test_collector.py"
echo "3. Check service logs: sudo journalctl -u plugwise-collector -f"
echo "4. View collected data: ls -la $APP_DIR/data/"
echo ""
echo "🔧 Service commands:"
echo "  Start:   sudo systemctl start plugwise-collector"
echo "  Stop:    sudo systemctl stop plugwise-collector"
echo "  Status:  sudo systemctl status plugwise-collector"
echo "  Restart: sudo systemctl restart plugwise-collector"
echo "" 