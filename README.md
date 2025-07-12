# Plugwise Data Collector

A Python-based data collector for Plugwise Stretch and Smile devices that extracts power usage data and meter readings, saving them to CSV files with daily rotation.

## Features

- 🔌 Real-time power consumption monitoring
- 📊 CSV data export with timestamps
- 🔄 Continuous data collection with configurable intervals
- 📈 Daily meter data collection (once per day)
- 🛡️ Error handling and retry logic
- 📝 Clean CLI interface
- 🗂️ Automatic daily file rotation
- 📋 Session files with date ranges
- ⚡ Graceful shutdown handling

## Installation

### Prerequisites

- Python 3.7+
- Network access to Plugwise devices
- Device credentials (username/password)

### Setup

#### macOS (Testing/Development)

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd plugwise_pi
   ```

2. **Run the macOS setup script:**
   ```bash
   ./setup_mac.sh
   ```

3. **Configure your devices:**
   Edit the configuration file:
   ```bash
   nano config.json
   ```

4. **Test the collector:**
   ```bash
   source venv/bin/activate
   python plugwise_collector.py --single
   ```

#### Raspberry Pi (Production)

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd plugwise_pi
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
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
       },
       "smile": {
         "ip": "192.168.178.18",
         "username": "smile",
         "password": "your_password",
         "port": 80,
         "enabled": true
       }
     }
   }
   ```

## Usage

### Main Collector

The main collector (`plugwise_collector.py`) handles both power usage and meter data:

#### Single Collection

Collect data once and save to CSV:
```bash
python plugwise_collector.py --single --output data/
```

#### Continuous Collection

Collect data every 60 seconds with daily file rotation:
```bash
python plugwise_collector.py --continuous --interval 60 --output data/
# Creates: power_usage_20250712.csv, power_usage_20250713.csv, etc.
```

#### Meter Data Collection

Control meter data collection:
```bash
# Collect power data only (no meter data)
python plugwise_collector.py --continuous --no-meters

# Collect both power and meter data (default)
python plugwise_collector.py --continuous

# Collect meter data only
python plugwise_collector.py --meters-only
```

### Daily Meter Collector

For Smile devices only, collect cumulative meter data once per day:
```bash
python daily_meter_collector.py --output data/
# Creates: daily_meters_20250712_20250712.csv
```

### Custom Configuration

Use a custom config file:
```bash
python plugwise_collector.py --config my_config.json --continuous
```

### Command Line Options

#### Main Collector
- `--config, -c`: Configuration file path
- `--interval, -i`: Collection interval in seconds (default: 60)
- `--output, -o`: Output directory (default: data)
- `--continuous, -C`: Run continuous collection
- `--single, -s`: Run single collection (default)
- `--no-meters`: Disable meter data collection
- `--meters-only`: Collect meter data only (no power data)

#### Daily Meter Collector
- `--config, -c`: Configuration file path
- `--output, -o`: Output directory (default: data)
- `--start-date`: Start date (YYYY-MM-DD, default: today)
- `--end-date`: End date (YYYY-MM-DD, default: today)

## Output Format

### Power Usage Data

Daily CSV files (00:00-23:59) with columns:
- `timestamp`: Collection timestamp
- `device`: Device name (stretch/smile)
- `appliance`: Appliance name
- `power_watts`: Current power consumption in Watts
- `measurement_timestamp`: Original measurement timestamp
- `module_id`: Plugwise module ID
- `meter_id`: Electricity meter ID

### Meter Data

Session CSV files with cumulative meter readings:
- `timestamp`: Collection timestamp
- `device`: Device name (smile)
- `electricity_consumed_peak_kwh`: Peak electricity consumption
- `electricity_consumed_off_peak_kwh`: Off-peak electricity consumption
- `electricity_produced_peak_kwh`: Peak electricity production
- `electricity_produced_off_peak_kwh`: Off-peak electricity production
- `gas_consumed_m3`: Gas consumption
- `net_electricity_kwh`: Net electricity consumption

### Daily Meter Data

Wide-format CSV files with one row per day:
- `date`: Date (YYYY-MM-DD)
- `electricity_consumed_peak_kwh`: Daily peak consumption
- `electricity_consumed_off_peak_kwh`: Daily off-peak consumption
- `electricity_produced_peak_kwh`: Daily peak production
- `electricity_produced_off_peak_kwh`: Daily off-peak production
- `gas_consumed_m3`: Daily gas consumption
- `net_electricity_kwh`: Daily net electricity

### File Naming
- **Daily power files**: `power_usage_YYYYMMDD.csv` (e.g., `power_usage_20250712.csv`)
- **Session meter files**: `meter_data_YYYYMMDD_HHMMSS_YYYYMMDD_HHMMSS.csv`
- **Daily meter files**: `daily_meters_YYYYMMDD_YYYYMMDD.csv`
- **Automatic rotation**: New files created each day at 00:00

## Data Collection Strategy

### Power Usage
- Collected continuously at specified intervals
- Real-time power consumption monitoring
- Daily file rotation

### Meter Data
- Collected once per day (at script start and midnight)
- Cumulative meter readings
- Session-based file naming with date ranges

## Raspberry Pi Deployment

### Deployment Options

#### Option 1: Systemd Service (Recommended)
Best for production - starts automatically on boot and restarts on failure.

#### Option 2: Manual Execution
Direct execution - good for testing and development.

### Systemd Service Setup (Option 1)

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

4. **File I/O errors:**
   - Check disk space
   - Verify file permissions
   - Ensure graceful shutdown

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