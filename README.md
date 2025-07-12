# Plugwise Data Collector

A Python-based data collector for Plugwise Stretch and Smile devices that extracts power usage data and saves it to CSV files.

## Features

- 🔌 Real-time power consumption monitoring
- 📊 CSV data export with timestamps
- 🔄 Continuous data collection with configurable intervals
- 🛡️ Error handling and retry logic
- 📝 Clean CLI interface

## Installation

### Prerequisites

- Python 3.7+
- Network access to Plugwise devices
- Device credentials (username/password)

### Setup

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd plugwise_pi
   ```

2. **Install dependencies:**
   ```bash
   ```

3. **Configure your devices:**
   Copy the example config and edit with your device details:
   ```bash
   cp config.example.json config.json
   nano config.json
   ```
   ```json
   {
     "devices": {
       "stretch": {
         "ip": "192.168.178.17",
         "username": "stretch",
         "password": "your_password",
         "port": 80,
         "enabled": true
       }
     }
   }
   ```

## Usage

### Single Collection

Collect data once and save to CSV:
```bash
python plugwise_collector.py --single --output data/
```

### Continuous Collection

Collect data every 60 seconds with daily file rotation:
```bash
python plugwise_collector.py --continuous --interval 60 --output data/
# Creates: power_usage_20250712.csv, power_usage_20250713.csv, etc.
```

### Custom Configuration

Use a custom config file:
```bash
python plugwise_collector.py --config my_config.json --continuous
```

### Command Line Options

- `--config, -c`: Configuration file path
- `--interval, -i`: Collection interval in seconds (default: 60)
- `--output, -o`: Output directory (default: data)
- `--continuous, -C`: Run continuous collection
- `--single, -s`: Run single collection (default)

## Output Format

The collector creates daily CSV files (00:00-23:59) with the following columns:
- `timestamp`: Collection timestamp
- `device`: Device name (stretch/smile)
- `appliance`: Appliance name
- `power_watts`: Current power consumption in Watts
- `measurement_timestamp`: Original measurement timestamp
- `module_id`: Plugwise module ID
- `meter_id`: Electricity meter ID

### File Naming
- **Daily files**: `power_usage_YYYYMMDD.csv` (e.g., `power_usage_20250712.csv`)
- **Automatic rotation**: New file created each day at 00:00
- **Continuous data**: All measurements for a day in single file

## Raspberry Pi Deployment

### System Service Setup

1. **Create a systemd service file:**
   ```bash
   sudo nano /etc/systemd/system/plugwise-collector.service
   ```

2. **Add the service configuration:**
   ```ini
   [Unit]
   Description=Plugwise Data Collector
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/plugwise_pi
   ExecStart=/usr/bin/python3 /home/pi/plugwise_pi/plugwise_collector.py --continuous --interval 60 --output /home/pi/plugwise_pi/data
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl enable plugwise-collector
   sudo systemctl start plugwise-collector
   sudo systemctl status plugwise-collector
   ```

### Logs

Check service logs:
```bash
sudo journalctl -u plugwise-collector -f
```

## Troubleshooting

### Common Issues

1. **Connection refused:**
   - Check device IP addresses in config
   - Verify network connectivity
   - Confirm device credentials

2. **No data collected:**
   - Verify devices are powered on
   - Check appliance mappings
   - Review XML structure changes

3. **Permission errors:**
   - Ensure output directory is writable
   - Check file permissions

### Debug Mode

Run with verbose output:
```bash
python plugwise_collector.py --single --output data/ 2>&1 | tee debug.log
```

## Configuration

### Device Configuration

Each device requires:
- `ip`: Device IP address
- `username`: Authentication username
- `password`: Authentication password
- `port`: HTTP port (usually 80)
- `enabled`: Enable/disable device

### Collection Settings

- `interval`: Collection frequency in seconds
- `timeout`: HTTP request timeout
- `retry_attempts`: Number of retry attempts

## License

This project is licensed under the MIT License. 