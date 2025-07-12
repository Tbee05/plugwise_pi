"""
Utility functions for Plugwise Pi.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import structlog


def setup_logging(config):
    """Setup logging configuration."""
    log_config = config.logging
    
    # Create logs directory if it doesn't exist
    log_file = Path(log_config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_config.level.upper()),
        format=log_config.format,
        handlers=[
            logging.FileHandler(log_config.file),
            logging.StreamHandler() if log_config.console else logging.NullHandler()
        ]
    )


def format_mac_address(mac: str) -> str:
    """Format MAC address to standard format."""
    # Remove any non-hex characters
    mac = ''.join(c for c in mac if c.isalnum())
    
    # Ensure it's 12 characters
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC address length: {len(mac)}")
    
    # Format as XX:XX:XX:XX:XX:XX
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2)).upper()


def validate_mac_address(mac: str) -> bool:
    """Validate MAC address format."""
    try:
        format_mac_address(mac)
        return True
    except ValueError:
        return False


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string to datetime object."""
    # Try common formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse timestamp: {timestamp_str}")


def safe_json_loads(data: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string."""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def calculate_power_consumption(watts: float, duration_hours: float) -> float:
    """Calculate energy consumption in kWh."""
    return (watts * duration_hours) / 1000


def format_power_consumption(kwh: float) -> str:
    """Format power consumption for display."""
    if kwh < 1:
        return f"{kwh * 1000:.1f} Wh"
    elif kwh < 1000:
        return f"{kwh:.2f} kWh"
    else:
        return f"{kwh / 1000:.2f} MWh"


def get_data_directory() -> Path:
    """Get the data directory path."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_logs_directory() -> Path:
    """Get the logs directory path."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def create_directories():
    """Create necessary directories."""
    get_data_directory()
    get_logs_directory()


def is_device_online(last_seen: datetime, threshold_seconds: int = 300) -> bool:
    """Check if device is online based on last seen timestamp."""
    if not last_seen:
        return False
    
    now = datetime.utcnow()
    time_diff = (now - last_seen).total_seconds()
    return time_diff <= threshold_seconds


def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Ensure it's not empty
    if not filename:
        filename = "unnamed"
    return filename 