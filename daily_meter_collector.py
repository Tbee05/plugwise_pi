#!/usr/bin/env python3
"""
Daily Meter Data Collector for Plugwise Devices
Collects cumulative meter readings once per day from Stretch and Smile devices
"""

import requests
import xml.etree.ElementTree as ET
import csv
import json
import time
import os
import sys
import argparse
from datetime import datetime, date, timedelta
from requests.auth import HTTPBasicAuth
from pathlib import Path

class DailyMeterCollector:
    """Daily meter data collector for Plugwise devices"""
    
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
                "timeout": 10,
                "retry_attempts": 3
            },
            "output": {
                "directory": "data",
                "filename_pattern": "meter_readings_{start_date}_{end_date}.csv"
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
    
    def extract_stretch_meter_data(self):
        """Extract cumulative meter data from Stretch device"""
        modules_xml = self.fetch_xml_data("stretch", "/core/modules")
        if not modules_xml:
            return None
        
        meter_data = {}
        
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
                        
                        # Get cumulative measurements
                        measurements = point_meter.findall(".//measurement")
                        for measurement in measurements:
                            directionality = measurement.get('directionality', '')
                            if directionality == 'consumed':
                                # This is cumulative consumption
                                cumulative_value = measurement.text.strip() if measurement.text else '0'
                                log_date = measurement.get('log_date', '')
                                
                                meter_data[appliance_name] = {
                                    'cumulative_kwh': float(cumulative_value) if cumulative_value.replace('.', '').replace('-', '').isdigit() else 0.0,
                                    'timestamp': log_date,
                                    'module_id': module_id,
                                    'meter_id': meter_id,
                                    'direction': 'consumed'
                                }
                                break
                        
        except Exception as e:
            print(f"❌ Error parsing Stretch XML: {e}")
        
        return meter_data
    
    def extract_smile_meter_data(self):
        """Extract cumulative meter data from Smile device"""
        domain_objects_xml = self.fetch_xml_data("smile", "/core/domain_objects")
        if not domain_objects_xml:
            return None
        
        try:
            root = ET.fromstring(domain_objects_xml)
            
            # Find the location (Home) which contains all the meter data
            location = root.find(".//location[@id='9ae235b74cf64a189acaccd033a1f59f']")
            if location is None:
                print("❌ Could not find Home location in Smile XML")
                return None
            
            meter_data = {}
            
            # Extract meter data from cumulative logs
            for cumulative_log in location.findall(".//cumulative_log"):
                log_type = cumulative_log.find('type')
                unit = cumulative_log.find('unit')
                
                if log_type is not None and unit is not None:
                    log_type_text = log_type.text
                    unit_text = unit.text
                    
                    # Get the most recent measurement
                    period = cumulative_log.find('period')
                    if period is not None:
                        # Process all measurements in the period (there can be multiple for different tariffs)
                        for measurement in period.findall('measurement'):
                            if measurement.text is not None:
                                value = float(measurement.text)
                                tariff = measurement.get('tariff', '')
                                log_date = measurement.get('log_date', '')
                                
                                # Store based on type and tariff
                                if log_type_text == 'electricity_consumed':
                                    if tariff == 'nl_peak':
                                        meter_data['electricity_consumed_peak'] = {
                                            'value': value,
                                            'unit': 'kWh',
                                            'timestamp': log_date,
                                            'type': 'electricity_consumed',
                                            'tariff': 'peak'
                                        }
                                    elif tariff == 'nl_offpeak':
                                        meter_data['electricity_consumed_offpeak'] = {
                                            'value': value,
                                            'unit': 'kWh',
                                            'timestamp': log_date,
                                            'type': 'electricity_consumed',
                                            'tariff': 'offpeak'
                                        }
                                elif log_type_text == 'electricity_produced':
                                    if tariff == 'nl_peak':
                                        meter_data['electricity_produced_peak'] = {
                                            'value': value,
                                            'unit': 'kWh',
                                            'timestamp': log_date,
                                            'type': 'electricity_produced',
                                            'tariff': 'peak'
                                        }
                                    elif tariff == 'nl_offpeak':
                                        meter_data['electricity_produced_offpeak'] = {
                                            'value': value,
                                            'unit': 'kWh',
                                            'timestamp': log_date,
                                            'type': 'electricity_produced',
                                            'tariff': 'offpeak'
                                        }
                                elif log_type_text == 'gas_consumed':
                                    meter_data['gas_consumed'] = {
                                        'value': value,
                                        'unit': 'm³',
                                        'timestamp': log_date,
                                        'type': 'gas_consumed',
                                        'tariff': ''
                                    }
            
            # Calculate totals
            total_consumed = 0
            total_produced = 0
            
            if 'electricity_consumed_peak' in meter_data:
                total_consumed += meter_data['electricity_consumed_peak']['value']
            if 'electricity_consumed_offpeak' in meter_data:
                total_consumed += meter_data['electricity_consumed_offpeak']['value']
            if 'electricity_produced_peak' in meter_data:
                total_produced += meter_data['electricity_produced_peak']['value']
            if 'electricity_produced_offpeak' in meter_data:
                total_produced += meter_data['electricity_produced_offpeak']['value']
            
            meter_data['electricity_total_consumed'] = {
                'value': total_consumed,
                'unit': 'kWh',
                'timestamp': datetime.now().isoformat(),
                'type': 'electricity_total_consumed',
                'tariff': ''
            }
            
            meter_data['electricity_total_produced'] = {
                'value': total_produced,
                'unit': 'kWh',
                'timestamp': datetime.now().isoformat(),
                'type': 'electricity_total_produced',
                'tariff': ''
            }
            
            meter_data['electricity_net_consumed'] = {
                'value': total_consumed - total_produced,
                'unit': 'kWh',
                'timestamp': datetime.now().isoformat(),
                'type': 'electricity_net_consumed',
                'tariff': ''
            }
            
            return meter_data
            
        except Exception as e:
            print(f"❌ Error parsing Smile XML: {e}")
            return None
    
    def collect_daily_meter_data(self):
        """Collect daily meter data from Smile device only"""
        print("📊 Collecting Daily Meter Data (Smile Only)")
        print("=" * 50)
        
        meter_data = {
            "collection_date": date.today().isoformat(),
            "collection_timestamp": datetime.now().isoformat(),
            "devices": {}
        }
        
        # Collect from Smile device only
        if "smile" in self.config["devices"]:
            smile_data = self.extract_smile_meter_data()
            if smile_data:
                meter_data["devices"]["smile"] = smile_data
                print("✅ Smile meter data collected")
            else:
                print("❌ Failed to collect Smile meter data")
        
        return meter_data
    
    def save_meter_data_to_csv(self, meter_data, output_dir, start_date=None, end_date=None):
        """Save meter data to wide format CSV file with date range in filename"""
        if not meter_data["devices"]:
            print("⚠️  No meter data to save")
            return None
        
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename with date range
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today()
        
        filename = os.path.join(
            output_dir, 
            f"meter_readings_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        )
        
        # Prepare wide format CSV data (one row per day)
        smile_data = meter_data["devices"].get("smile", {})
        
        if smile_data:
            # Create one row with all meter values
            row_data = {
                'date': meter_data["collection_date"],
                'timestamp': meter_data["collection_timestamp"]
            }
            
            # Add each meter type as a column
            for meter_type, meter_info in smile_data.items():
                if isinstance(meter_info, dict) and 'value' in meter_info:
                    # Use meter_type as column name
                    row_data[meter_type] = meter_info['value']
            
            # Write to CSV
            fieldnames = ['date', 'timestamp']
            
            # Add meter columns in a consistent order
            meter_columns = [
                'gas_consumed',
                'electricity_consumed_peak', 
                'electricity_consumed_offpeak',
                'electricity_produced_peak',
                'electricity_produced_offpeak',
                'electricity_total_consumed',
                'electricity_total_produced',
                'electricity_net_consumed'
            ]
            
            # Add meter columns
            for meter_col in meter_columns:
                if meter_col in row_data:
                    fieldnames.append(meter_col)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(row_data)
            
            print(f"✅ Saved daily meter readings to: {filename}")
            return filename
        
        return None
    
    def print_meter_summary(self, meter_data):
        """Print a nice summary of daily meter readings"""
        print(f"\n📊 Daily Meter Readings - {meter_data['collection_date']}")
        print("=" * 60)
        
        smile_data = meter_data["devices"].get("smile", {})
        
        if smile_data:
            print(f"\n🔌 SMILE METER READINGS:")
            
            # Display in organized groups
            print("  Electricity Consumption:")
            if 'electricity_consumed_peak' in smile_data:
                value = smile_data['electricity_consumed_peak']['value']
                print(f"    Peak:     {value:12.2f} kWh")
            if 'electricity_consumed_offpeak' in smile_data:
                value = smile_data['electricity_consumed_offpeak']['value']
                print(f"    Off-peak: {value:12.2f} kWh")
            if 'electricity_total_consumed' in smile_data:
                value = smile_data['electricity_total_consumed']['value']
                print(f"    Total:    {value:12.2f} kWh")
            
            print("  Electricity Production:")
            if 'electricity_produced_peak' in smile_data:
                value = smile_data['electricity_produced_peak']['value']
                print(f"    Peak:     {value:12.2f} kWh")
            if 'electricity_produced_offpeak' in smile_data:
                value = smile_data['electricity_produced_offpeak']['value']
                print(f"    Off-peak: {value:12.2f} kWh")
            if 'electricity_total_produced' in smile_data:
                value = smile_data['electricity_total_produced']['value']
                print(f"    Total:    {value:12.2f} kWh")
            
            print("  Summary:")
            if 'electricity_net_consumed' in smile_data:
                value = smile_data['electricity_net_consumed']['value']
                print(f"    Net:      {value:12.2f} kWh")
            if 'gas_consumed' in smile_data:
                value = smile_data['gas_consumed']['value']
                print(f"    Gas:      {value:12.2f} m³")
        
        print("=" * 60)
    
    def run_daily_collection(self, output_dir=None, start_date=None, end_date=None):
        """Run daily meter data collection"""
        print("📊 Daily Meter Data Collector")
        print("=" * 50)
        
        # Collect meter data
        meter_data = self.collect_daily_meter_data()
        
        if meter_data["devices"]:
            # Print summary
            self.print_meter_summary(meter_data)
            
            # Save to file
            if output_dir:
                self.save_meter_data_to_csv(meter_data, output_dir, start_date, end_date)
            
            return meter_data
        else:
            print("❌ No meter data collected")
            return None

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Daily Meter Data Collector")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--output", "-o", default="data", 
                       help="Output directory (default: data)")
    parser.add_argument("--start-date", "-s", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", "-e", help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    # Parse dates if provided
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        except ValueError:
            print("❌ Invalid start date format. Use YYYY-MM-DD")
            return
    
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        except ValueError:
            print("❌ Invalid end date format. Use YYYY-MM-DD")
            return
    
    # Create collector
    collector = DailyMeterCollector(args.config)
    
    # Run collection
    collector.run_daily_collection(args.output, start_date, end_date)

if __name__ == "__main__":
    main() 