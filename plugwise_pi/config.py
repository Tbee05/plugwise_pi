"""
Configuration management for Plugwise Pi.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class PlugwiseNetworkConfig(BaseModel):
    """Network configuration for Plugwise devices."""
    interface: str = "eth0"
    timeout: int = 30
    retry_attempts: int = 3


class PlugwiseDeviceConfig(BaseModel):
    """Configuration for a single Plugwise device."""
    name: str
    mac_address: str
    type: str = "circle"
    location: Optional[str] = None
    description: Optional[str] = None


class PlugwiseCollectionConfig(BaseModel):
    """Data collection configuration."""
    interval: int = 60
    batch_size: int = 100
    max_retries: int = 3


class PlugwiseConfig(BaseModel):
    """Main Plugwise configuration."""
    network: PlugwiseNetworkConfig = Field(default_factory=PlugwiseNetworkConfig)
    devices: list[PlugwiseDeviceConfig] = []
    collection: PlugwiseCollectionConfig = Field(default_factory=PlugwiseCollectionConfig)


class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = "sqlite"
    sqlite: Dict[str, Any] = Field(default_factory=lambda: {"path": "data/plugwise.db", "timeout": 30})
    postgresql: Optional[Dict[str, Any]] = None


class APIConfig(BaseModel):
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=list)
    rate_limit: Dict[str, int] = Field(default_factory=lambda: {"requests_per_minute": 100, "burst_size": 20})


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/plugwise.log"
    max_size: str = "10MB"
    backup_count: int = 5
    console: bool = True


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    enabled: bool = True
    prometheus_port: int = 9090
    health_check_interval: int = 300
    alerts: Dict[str, int] = Field(default_factory=lambda: {
        "device_offline_threshold": 300,
        "high_power_threshold": 5000,
        "low_battery_threshold": 20
    })


class DataManagementConfig(BaseModel):
    """Data management configuration."""
    retention_days: int = 365
    cleanup_interval: int = 86400
    compression_enabled: bool = True


class SecurityConfig(BaseModel):
    """Security configuration."""
    api_key_required: bool = False
    allowed_ips: list[str] = Field(default_factory=list)
    ssl_enabled: bool = False


class DevelopmentConfig(BaseModel):
    """Development configuration."""
    mock_devices: bool = False
    fake_data: bool = False
    verbose_logging: bool = False


class Config(BaseModel):
    """Main configuration class."""
    plugwise: PlugwiseConfig = Field(default_factory=PlugwiseConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    data_management: DataManagementConfig = Field(default_factory=DataManagementConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.yaml"
        self._config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load configuration from YAML file."""
        if self._config is not None:
            return self._config
        
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.warning(f"Configuration file {self.config_path} not found. Using default configuration.")
            self._config = Config()
            return self._config
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self._config = Config(**config_data)
            logger.info(f"Configuration loaded from {self.config_path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            self._config = Config()
            return self._config
    
    def get_config(self) -> Config:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> Config:
        """Reload configuration from file."""
        self._config = None
        return self.load_config()


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config_manager.get_config()


def reload_config() -> Config:
    """Reload the global configuration."""
    return config_manager.reload_config() 