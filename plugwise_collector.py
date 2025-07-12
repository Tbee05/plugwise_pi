#!/usr/bin/env python3
"""
Plugwise Data Collector for Raspberry Pi
Collects power usage data from Plugwise Stretch and Smile devices
"""

import requests
import xml.etree.ElementTree as ET
import csv
import json
import time
import os
import sys
import argparse
from datetime import datetime
from requests.auth import HTTPBasicAuth
from pathlib import Path

class PlugwiseCollector:
    """Main collector class for Plugwise devices"""
    
    def __init__(self, config_file=None):
        """Initialize the collector with configuration"""
        self.config = self.load_config(config_file)
        self.appliance_mapping = {}
        
    def load_config(self, config_file=None):
        """Load configuration from file or use defaults"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "devices": {
                "stretch": {
                    "ip": "192.168.178.17",
                    "username": "stretch",
                    "password": "kjzpttgh",
                    "port": 80,
                    "enabled": True
                },
                "smile": {
                    "ip": "192.168.178.35", 
                    "username": "smile",
                    "password": "kngzthgf",
                    "port": 80,
                    "enabled": True
                }
            },
            "collection": {
                "interval": 60,  # seconds
                "timeout": 10,
                "retry_attempts": 3
            },
            "output": {
                "format": "csv",
                "directory": "data",
                "filename_pattern": "power_usage_{timestamp}.csv"
            }
        }
    
    def fetch_xml_data(self, device_name, endpoint):
        """Fetch XML data from a specific device endpoint"""
        device_config = self.config["devices"][device_name]
        
        if not device_config.get("enabled", True):
            return None
            
        url = f"http://{device_config['ip']}:{device_config['port']}{endpoint}"
        auth = HTTPBasicAuth(device_config['username'], device_config['password'])
        
        for attempt in range(self.config["collection"]["retry_attempts"]):
            try:
                response = requests.get(
                    url, 
                    auth=auth, 
                    timeout=self.config["collection"]["timeout"]
                )
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"❌ {device_name} {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {device_name} {endpoint} (attempt {attempt + 1}): {e}")
                if attempt < self.config["collection"]["retry_attempts"] - 1:
                    time.sleep(1)
        
        return None
    
    def build_appliance_mapping(self):
        """Build mapping between appliances and their modules/services"""
        print("🔗 Building appliance-module mapping...")
        
        appliances_xml = self.fetch_xml_data("stretch", "/core/appliances")
        if not appliances_xml:
            print("❌ Failed to fetch appliances data")
            return {}
        
        mapping = {}
        try:
            root = ET.fromstring(appliances_xml)
            
            for appliance in root.findall(".//appliance"):
                appliance_id = appliance.get('id', '')
                name_elem = appliance.find('name')
                name = name_elem.text.strip() if name_elem is not None and name_elem.text else 'Unknown'
                
                # Find all services for this appliance
                services = appliance.findall(".//services/*")
                for service in services:
                    service_id = service.get('id', '')
                    service_type = service.tag
                    
                    if service_type == 'electricity_point_meter':
                        mapping[service_id] = {
                            'appliance_name': name,
                            'appliance_id': appliance_id,
                            'service_type': service_type
                        }
                        
        except Exception as e:
            print(f"❌ Error building appliance mapping: {e}")
        
        print(f"✅ Found {len(mapping)} appliance-meter mappings")
        return mapping
    
    def extract_power_measurements(self):
        """Extract current power measurements from all devices"""
        power_data = {
            "timestamp": datetime.now().isoformat(),
            "devices": {}
        }
        
        # Get appliance mapping for Stretch
        if not self.appliance_mapping:
            self.appliance_mapping = self.build_appliance_mapping()
        
        # Collect from Stretch device
        if "stretch" in self.config["devices"]:
            stretch_data = self.extract_stretch_power()
            if stretch_data:
                power_data["devices"]["stretch"] = stretch_data
        
        # Collect from Smile device (if needed)
        if "smile" in self.config["devices"]:
            smile_data = self.extract_smile_power()
            if smile_data:
                power_data["devices"]["smile"] = smile_data
        
        return power_data
    
    def extract_stretch_power(self):
        """Extract power measurements from Stretch device"""
        modules_xml = self.fetch_xml_data("stretch", "/core/modules")
        if not modules_xml:
            return None
        
        power_data = {}
        
        try:
            root = ET.fromstring(modules_xml)
            
            # Find all modules
            for module in root.findall(".//module"):
                module_id = module.get('id', '')
                
                # Find electricity_point_meter for this module
                point_meters = module.findall(".//electricity_point_meter")
                
                for point_meter in point_meters:
                    meter_id = point_meter.get('id', '')
                    
                    # Check if this meter is associated with an appliance
                    if meter_id in self.appliance_mapping:
                        appliance_info = self.appliance_mapping[meter_id]
                        appliance_name = appliance_info['appliance_name']
                        
                        # Get the latest measurement (consumed power)
                        measurements = point_meter.findall(".//measurement")
                        for measurement in measurements:
                            directionality = measurement.get('directionality', '')
                            if directionality == 'consumed':
                                power_value = measurement.text.strip() if measurement.text else '0'
                                log_date = measurement.get('log_date', '')
                                
                                power_data[appliance_name] = {
                                    'power_watts': float(power_value) if power_value.replace('.', '').replace('-', '').isdigit() else 0.0,
                                    'timestamp': log_date,
                                    'module_id': module_id,
                                    'meter_id': meter_id
                                }
                                break
                        
        except Exception as e:
            print(f"❌ Error parsing Stretch XML: {e}")
        
        return power_data
    
    def extract_smile_power(self):
        """Extract power measurements from Smile device"""
        # For now, just return basic structure
        # Smile has different data structure - can be extended later
        return {"status": "not_implemented"}
    
    def save_to_csv(self, power_data, output_dir):
        """Save power data to CSV file"""
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"power_usage_{timestamp}.csv")
        
        # Prepare CSV data
        csv_data = []
        for device_name, device_data in power_data["devices"].items():
            if isinstance(device_data, dict) and device_data:
                for appliance_name, appliance_data in device_data.items():
                    if isinstance(appliance_data, dict) and 'power_watts' in appliance_data:
                        csv_data.append({
                            'timestamp': power_data["timestamp"],
                            'device': device_name,
                            'appliance': appliance_name,
                            'power_watts': appliance_data['power_watts'],
                            'measurement_timestamp': appliance_data.get('timestamp', ''),
                            'module_id': appliance_data.get('module_id', ''),
                            'meter_id': appliance_data.get('meter_id', '')
                        })
        
        if csv_data:
            # Get all unique keys
            fieldnames = ['timestamp', 'device', 'appliance', 'power_watts', 'measurement_timestamp', 'module_id', 'meter_id']
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            print(f"✅ Saved {len(csv_data)} measurements to: {filename}")
            return filename
        else:
            print("⚠️  No power data to save")
            return None
    
    def print_power_summary(self, power_data):
        """Print a nice summary of current power usage"""
        print(f"\n📊 Current Power Usage - {power_data['timestamp']}")
        print("=" * 60)
        
        total_power = 0.0
        
        for device_name, device_data in power_data["devices"].items():
            if isinstance(device_data, dict) and device_data:
                print(f"\n🔌 {device_name.upper()}:")
                device_total = 0.0
                
                for appliance_name, appliance_data in device_data.items():
                    if isinstance(appliance_data, dict) and 'power_watts' in appliance_data:
                        power = appliance_data['power_watts']
                        device_total += power
                        print(f"  {appliance_name:25} : {power:8.2f} W")
                
                print(f"  {'TOTAL':25} : {device_total:8.2f} W")
                total_power += device_total
        
        print("=" * 60)
        print(f"  GRAND TOTAL POWER USAGE : {total_power:8.2f} W")
        print("=" * 60)
    
    def run_single_collection(self, output_dir=None):
        """Run a single data collection cycle"""
        print("🔌 Plugwise Data Collector")
        print("=" * 50)
        
        # Extract power measurements
        power_data = self.extract_power_measurements()
        
        if power_data["devices"]:
            # Print summary
            self.print_power_summary(power_data)
            
            # Save to file
            if output_dir:
                self.save_to_csv(power_data, output_dir)
            
            return power_data
        else:
            print("❌ No power data collected")
            return None
    
    def run_continuous_collection(self, interval, output_dir=None):
        """Run continuous data collection"""
        print(f"🔄 Starting continuous collection (interval: {interval}s)")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        try:
            while True:
                self.run_single_collection(output_dir)
                print(f"⏰ Waiting {interval} seconds until next collection...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Collection stopped by user")
        except Exception as e:
            print(f"\n❌ Collection error: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Plugwise Data Collector")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--interval", "-i", type=int, default=60, 
                       help="Collection interval in seconds (default: 60)")
    parser.add_argument("--output", "-o", default="data", 
                       help="Output directory (default: data)")
    parser.add_argument("--continuous", "-C", action="store_true",
                       help="Run continuous collection")
    parser.add_argument("--single", "-s", action="store_true",
                       help="Run single collection (default)")
    
    args = parser.parse_args()
    
    # Create collector
    collector = PlugwiseCollector(args.config)
    
    # Run collection
    if args.continuous:
        collector.run_continuous_collection(args.interval, args.output)
    else:
        collector.run_single_collection(args.output)

if __name__ == "__main__":
    main() 