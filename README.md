# Plugwise Pi - Domotics Data Collection System

A Python-based system for collecting and managing data from Plugwise domotics devices on Raspberry Pi.

## Overview

This project provides tools and utilities to:
- Connect to Plugwise domotics devices
- Collect sensor data and energy consumption metrics
- Store and manage data efficiently
- Provide APIs for data access
- Monitor system health and performance

## Features

- **Data Collection**: Automated collection from Plugwise devices
- **Data Storage**: Efficient local storage with SQLite/PostgreSQL options
- **API Interface**: RESTful API for data access
- **Monitoring**: System health and performance monitoring
- **Configuration**: Flexible configuration management
- **Logging**: Comprehensive logging system

## Requirements

- Python 3.8+
- Raspberry Pi (tested on Pi 4)
- Plugwise domotics devices
- Network connectivity

## Installation

### Prerequisites

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3 python3-pip python3-venv

# Install additional system dependencies
sudo apt install sqlite3 postgresql-client
```

### Project Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd plugwise_pi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp config/config.example.yaml config/config.yaml

# Edit configuration
nano config/config.yaml
```

## Configuration

Edit `config/config.yaml` to configure your Plugwise devices and system settings:

```yaml
# Plugwise device configuration
plugwise:
  devices:
    - name: "Living Room"
      mac_address: "00:01:02:03:04:05"
      type: "circle"
    - name: "Kitchen"
      mac_address: "00:01:02:03:04:06"
      type: "circle"

# Database configuration
database:
  type: "sqlite"  # or "postgresql"
  path: "data/plugwise.db"
  # For PostgreSQL:
  # host: "localhost"
  # port: 5432
  # name: "plugwise"
  # user: "plugwise_user"
  # password: "your_password"

# API configuration
api:
  host: "0.0.0.0"
  port: 8080
  debug: false

# Logging configuration
logging:
  level: "INFO"
  file: "logs/plugwise.log"
  max_size: "10MB"
  backup_count: 5
```

## Usage

### Starting the Data Collector

```bash
# Activate virtual environment
source venv/bin/activate

# Start data collection
python -m plugwise_pi.collector
```

### Starting the API Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start API server
python -m plugwise_pi.api
```

### Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/
```

## Project Structure

```
plugwise_pi/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── setup.py                 # Package setup
├── config/                  # Configuration files
│   ├── config.example.yaml  # Example configuration
│   └── config.yaml          # Your configuration (create from example)
├── plugwise_pi/            # Main package
│   ├── __init__.py
│   ├── collector.py         # Data collection module
│   ├── api.py              # API server
│   ├── database.py          # Database operations
│   ├── models.py            # Data models
│   └── utils.py             # Utility functions
├── tests/                   # Test files
│   ├── __init__.py
│   ├── test_collector.py
│   ├── test_api.py
│   └── test_database.py
├── data/                    # Data storage (created automatically)
├── logs/                    # Log files (created automatically)
└── docs/                    # Documentation
    └── api.md              # API documentation
```

## Development

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

### Code Style

This project follows PEP 8 style guidelines. Use `black` for code formatting:

```bash
pip install black
black plugwise_pi/ tests/
```

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure proper file permissions
2. **Database connection failed**: Check database configuration
3. **Device not found**: Verify MAC addresses and network connectivity

### Logs

Check logs in the `logs/` directory for detailed error information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Create an issue in the repository
- Check the documentation in `docs/`
- Review the logs for error details 