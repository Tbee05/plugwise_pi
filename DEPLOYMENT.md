# Plugwise Pi Deployment Guide

This guide provides step-by-step instructions for deploying the Plugwise Pi project on your Raspberry Pi.

## Prerequisites

- Raspberry Pi (tested on Pi 4)
- Internet connection
- SSH access to your Raspberry Pi
- Plugwise domotics devices

## Quick Start

### 1. Clone the Repository

```bash
# On your development machine
git clone <your-repository-url>
cd plugwise_pi

# Push to your remote repository
git remote add origin <your-repository-url>
git push -u origin main
```

### 2. Deploy to Raspberry Pi

#### Option A: Using the deployment script (Recommended)

```bash
# Copy the project to your Raspberry Pi
scp -r . pi@YOUR_PI_IP:/home/pi/plugwise_pi

# SSH into your Raspberry Pi
ssh pi@YOUR_PI_IP

# Run the deployment script
cd /home/pi/plugwise_pi
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

#### Option B: Manual deployment

```bash
# SSH into your Raspberry Pi
ssh pi@YOUR_PI_IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv sqlite3 git

# Clone your repository
git clone <your-repository-url> /home/pi/plugwise_pi
cd /home/pi/plugwise_pi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p data logs

# Copy configuration
cp config/config.example.yaml config/config.yaml
```

### 3. Configure Your Devices

Edit the configuration file with your Plugwise device settings:

```bash
nano config/config.yaml
```

Update the device configuration section:

```yaml
plugwise:
  devices:
    - name: "Living Room Circle"
      mac_address: "00:01:02:03:04:05"  # Your device MAC address
      type: "circle"
      location: "Living Room"
      description: "Main living room power monitoring"
```

### 4. Install System Services

```bash
# Copy systemd service files
sudo cp systemd/plugwise-pi.service /etc/systemd/system/
sudo cp systemd/plugwise-pi-api.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable plugwise-pi.service
sudo systemctl enable plugwise-pi-api.service
```

### 5. Start the Services

```bash
# Start the data collector
sudo systemctl start plugwise-pi.service

# Start the API server
sudo systemctl start plugwise-pi-api.service

# Check status
sudo systemctl status plugwise-pi.service
sudo systemctl status plugwise-pi-api.service
```

### 6. Verify Installation

```bash
# Check if services are running
sudo systemctl is-active plugwise-pi.service
sudo systemctl is-active plugwise-pi-api.service

# View logs
tail -f /home/pi/plugwise_pi/logs/plugwise.log

# Test API
curl http://localhost:8080/health
```

## Configuration

### Device Configuration

Edit `config/config.yaml` to configure your Plugwise devices:

```yaml
plugwise:
  devices:
    - name: "Device Name"
      mac_address: "XX:XX:XX:XX:XX:XX"
      type: "circle"
      location: "Location"
      description: "Description"
```

### Network Configuration

```yaml
plugwise:
  network:
    interface: "eth0"  # or "wlan0" for WiFi
    timeout: 30
    retry_attempts: 3
```

### API Configuration

```yaml
api:
  host: "0.0.0.0"  # Bind to all interfaces
  port: 8080
  debug: false
```

## Usage

### Manual Operation

```bash
# Activate virtual environment
source venv/bin/activate

# Run data collector
python -m plugwise_pi.collector

# Run API server
python -m plugwise_pi.api
```

### Service Management

```bash
# Start services
sudo systemctl start plugwise-pi.service
sudo systemctl start plugwise-pi-api.service

# Stop services
sudo systemctl stop plugwise-pi.service
sudo systemctl stop plugwise-pi-api.service

# Restart services
sudo systemctl restart plugwise-pi.service
sudo systemctl restart plugwise-pi-api.service

# View logs
sudo journalctl -u plugwise-pi.service -f
sudo journalctl -u plugwise-pi-api.service -f
```

### API Usage

Once the API server is running, you can access:

- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health
- **Devices**: http://localhost:8080/devices
- **Readings**: http://localhost:8080/devices/{device_id}/readings

### Example API Calls

```bash
# Get all devices
curl http://localhost:8080/devices

# Get latest reading for device 1
curl http://localhost:8080/devices/1/readings/latest

# Get readings for the last hour
curl "http://localhost:8080/devices/1/readings?start_time=2024-01-01T11:00:00Z&end_time=2024-01-01T12:00:00Z"
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check service status
   sudo systemctl status plugwise-pi.service
   
   # View detailed logs
   sudo journalctl -u plugwise-pi.service -n 50
   ```

2. **Permission denied**
   ```bash
   # Fix permissions
   sudo chown -R pi:pi /home/pi/plugwise_pi
   chmod +x scripts/deploy.sh
   ```

3. **Database errors**
   ```bash
   # Check database file
   ls -la /home/pi/plugwise_pi/data/
   
   # Recreate database (if needed)
   rm /home/pi/plugwise_pi/data/plugwise.db
   ```

4. **Network connectivity issues**
   ```bash
   # Check network interface
   ip addr show
   
   # Test device connectivity
   ping YOUR_DEVICE_IP
   ```

### Log Files

- **Application logs**: `/home/pi/plugwise_pi/logs/plugwise.log`
- **System logs**: `sudo journalctl -u plugwise-pi.service`
- **API logs**: `sudo journalctl -u plugwise-pi-api.service`

### Debug Mode

Enable debug logging in `config/config.yaml`:

```yaml
logging:
  level: "DEBUG"
  console: true
```

## Updates

### Automatic Updates

```bash
# Pull latest changes
cd /home/pi/plugwise_pi
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart plugwise-pi.service
sudo systemctl restart plugwise-pi-api.service
```

### Manual Updates

```bash
# Stop services
sudo systemctl stop plugwise-pi.service
sudo systemctl stop plugwise-pi-api.service

# Update code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Start services
sudo systemctl start plugwise-pi.service
sudo systemctl start plugwise-pi-api.service
```

## Security Considerations

1. **Firewall**: Configure firewall to only allow necessary ports
2. **SSH**: Use key-based authentication
3. **Updates**: Keep system and dependencies updated
4. **Monitoring**: Monitor logs for unusual activity

## Support

For issues and questions:

1. Check the logs: `tail -f /home/pi/plugwise_pi/logs/plugwise.log`
2. Review the API documentation: http://localhost:8080/docs
3. Check service status: `sudo systemctl status plugwise-pi.service`
4. Create an issue in the repository

## Next Steps

1. **Add more devices**: Configure additional Plugwise devices
2. **Set up monitoring**: Configure alerts and notifications
3. **Create dashboards**: Build web interfaces for data visualization
4. **Integrate with other systems**: Connect to Home Assistant, Grafana, etc. 