"""
Data collector for Plugwise devices.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from .config import get_config
from .database import db_manager
from .utils import setup_logging, create_directories

logger = logging.getLogger(__name__)


class PlugwiseCollector:
    """Collects data from Plugwise devices."""
    
    def __init__(self):
        self.config = get_config()
        self.running = False
        self._setup()
    
    def _setup(self):
        """Setup the collector."""
        setup_logging(self.config)
        create_directories()
        logger.info("Plugwise collector initialized")
    
    def start(self):
        """Start the data collection process."""
        self.running = True
        logger.info("Starting Plugwise data collection")
        
        try:
            while self.running:
                self._collect_data()
                time.sleep(self.config.plugwise.collection.interval)
        except KeyboardInterrupt:
            logger.info("Stopping collector due to keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in collector: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the data collection process."""
        self.running = False
        logger.info("Plugwise collector stopped")
    
    def _collect_data(self):
        """Collect data from all configured devices."""
        devices = self.config.plugwise.devices
        
        for device_config in devices:
            try:
                self._collect_device_data(device_config)
            except Exception as e:
                logger.error(f"Error collecting data from {device_config.name}: {e}")
    
    def _collect_device_data(self, device_config):
        """Collect data from a single device."""
        # TODO: Implement actual Plugwise device communication
        # This is a placeholder for the actual implementation
        
        # Check if device exists in database
        device = db_manager.get_device_by_mac(device_config.mac_address)
        if not device:
            # Add device to database
            device = db_manager.add_device(
                name=device_config.name,
                mac_address=device_config.mac_address,
                device_type=device_config.type,
                location=device_config.location,
                description=device_config.description
            )
        
        # TODO: Replace with actual device communication
        # For now, we'll create mock data
        if self.config.development.fake_data:
            self._collect_mock_data(device)
        else:
            self._collect_real_data(device)
    
    def _collect_mock_data(self, device):
        """Collect mock data for development/testing."""
        import random
        
        # Generate mock readings
        power_watts = random.uniform(0, 2000)
        energy_kwh = power_watts / 1000 * (self.config.plugwise.collection.interval / 3600)
        temperature = random.uniform(18, 25)
        humidity = random.uniform(40, 60)
        battery = random.uniform(80, 100)
        
        # Add reading to database
        reading = db_manager.add_reading(
            device_id=device.id,
            power_watts=power_watts,
            energy_kwh=energy_kwh,
            temperature_celsius=temperature,
            humidity_percent=humidity,
            battery_percent=battery,
            is_online=True,
            raw_data=f'{{"mock": true, "timestamp": "{datetime.utcnow().isoformat()}"}}'
        )
        
        logger.debug(f"Mock data collected for {device.name}: {power_watts:.1f}W")
    
    def _collect_real_data(self, device):
        """Collect real data from Plugwise device."""
        # TODO: Implement actual Plugwise device communication
        # This will involve:
        # 1. Connecting to the Plugwise network
        # 2. Sending commands to the device
        # 3. Parsing the response
        # 4. Storing the data
        
        logger.warning(f"Real data collection not yet implemented for {device.name}")
        
        # For now, just log that we would collect data
        logger.info(f"Would collect data from {device.name} ({device.mac_address})")


def main():
    """Main entry point for the collector."""
    collector = PlugwiseCollector()
    collector.start()


if __name__ == "__main__":
    main() 