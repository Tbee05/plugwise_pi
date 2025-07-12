"""
Tests for configuration module.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from plugwise_pi.config import Config, ConfigManager


def test_default_config():
    """Test default configuration creation."""
    config = Config()
    
    assert config.plugwise.network.interface == "eth0"
    assert config.plugwise.network.timeout == 30
    assert config.database.type == "sqlite"
    assert config.api.host == "0.0.0.0"
    assert config.api.port == 8080


def test_config_manager():
    """Test configuration manager."""
    manager = ConfigManager()
    config = manager.get_config()
    
    assert isinstance(config, Config)
    assert config.plugwise.network.interface == "eth0"


def test_config_loading():
    """Test configuration loading from file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        test_config = {
            'plugwise': {
                'network': {
                    'interface': 'wlan0',
                    'timeout': 60
                },
                'devices': [
                    {
                        'name': 'Test Device',
                        'mac_address': '00:11:22:33:44:55',
                        'type': 'circle'
                    }
                ]
            },
            'api': {
                'port': 9090
            }
        }
        yaml.dump(test_config, f)
        config_file = f.name
    
    try:
        manager = ConfigManager(config_file)
        config = manager.load_config()
        
        assert config.plugwise.network.interface == "wlan0"
        assert config.plugwise.network.timeout == 60
        assert config.api.port == 9090
        assert len(config.plugwise.devices) == 1
        assert config.plugwise.devices[0].name == "Test Device"
    finally:
        Path(config_file).unlink(missing_ok=True)


def test_device_config():
    """Test device configuration."""
    from plugwise_pi.config import PlugwiseDeviceConfig
    
    device = PlugwiseDeviceConfig(
        name="Test Device",
        mac_address="00:11:22:33:44:55",
        type="circle",
        location="Living Room"
    )
    
    assert device.name == "Test Device"
    assert device.mac_address == "00:11:22:33:44:55"
    assert device.type == "circle"
    assert device.location == "Living Room" 