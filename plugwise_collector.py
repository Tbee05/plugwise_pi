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
from datetime import datetime, date
from requests.auth import HTTPBasicAuth
from pathlib import Path

class PlugwiseCollector:
    """Main collector class for Plugwise devices"""
    
    def __init__(self, config_file=None):
        """Initialize the collector with configuration"""
        self.config = self.load_config(config_file)
        self.appliance_mapping = {}
        self.current_csv_file = None
        self.current_csv_writer = None
        self.current_date = None
        self.collect_meter_data = True
        self.session_start_date = None
        self.session_meter_file = None
        self.shutdown_requested = False
        self.last_meter_collection_date = None
        
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
                "filename_pattern": "power_usage_{date}.csv"
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
        """Extract power measurements and meter data from Smile device"""
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
            
            # Extract current power usage (point_log with electricity_consumed)
            current_power = 0.0
            current_timestamp = None
            peak_power = 0.0
            offpeak_power = 0.0
            active_tariff = None
            
            for point_log in location.findall(".//point_log"):
                log_type = point_log.find('type')
                if log_type is not None and log_type.text == 'electricity_consumed':
                    unit = point_log.find('unit')
                    if unit is not None and unit.text == 'W':
                        # Get the most recent measurement - sum all tariff values
                        period = point_log.find('period')
                        if period is not None:
                            for measurement in period.findall('measurement'):
                                if measurement.text is not None:
                                    power_value = float(measurement.text)
                                    tariff = measurement.get('tariff', '')
                                    
                                    if tariff == 'nl_peak':
                                        peak_power = power_value
                                    elif tariff == 'nl_offpeak':
                                        offpeak_power = power_value
                                    
                                    current_power += power_value
                                    if current_timestamp is None:
                                        current_timestamp = measurement.get('log_date')
                            
                            # Determine active tariff
                            if peak_power > 0 and offpeak_power == 0:
                                active_tariff = 'peak'
                            elif offpeak_power > 0 and peak_power == 0:
                                active_tariff = 'off-peak'
                            elif peak_power > 0 and offpeak_power > 0:
                                active_tariff = 'both'
                            else:
                                active_tariff = 'none'
                            break
            
            # Extract meter data from cumulative logs
            meter_data = {}
            
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
                                
                                # Store based on type and tariff
                                if log_type_text == 'electricity_consumed':
                                    if tariff == 'nl_peak':
                                        meter_data['usage_high'] = value
                                    elif tariff == 'nl_offpeak':
                                        meter_data['usage_low'] = value
                                elif log_type_text == 'electricity_produced':
                                    if tariff == 'nl_peak':
                                        meter_data['production_high'] = value
                                    elif tariff == 'nl_offpeak':
                                        meter_data['production_low'] = value
                                elif log_type_text == 'gas_consumed':
                                    meter_data['gas'] = value
            
            # Calculate net consumption (usage - production)
            net_consumption = 0
            if 'usage_high' in meter_data and 'usage_low' in meter_data:
                net_consumption += meter_data['usage_high'] + meter_data['usage_low']
            if 'production_high' in meter_data and 'production_low' in meter_data:
                net_consumption -= meter_data['production_high'] + meter_data['production_low']
            
            meter_data['net_consumption'] = net_consumption
            
            # Return structured data
            return {
                'current_power': {
                    'total_watts': current_power,
                    'peak_watts': peak_power,
                    'offpeak_watts': offpeak_power,
                    'active_tariff': active_tariff,
                    'timestamp': current_timestamp
                },
                'meter_data': meter_data
            }
            
        except Exception as e:
            print(f"❌ Error parsing Smile XML: {e}")
            return None
    
    def extract_smile_meter_data(self):
        """Extract cumulative meter data from Smile device for daily collection"""
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
        """Collect daily meter data from Smile device"""
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
    
    def get_session_meter_file(self, output_dir):
        """Get or create session meter CSV file"""
        # Initialize session start date if not set
        if self.session_start_date is None:
            self.session_start_date = date.today()
        
        # Create session file if it doesn't exist
        if self.session_meter_file is None:
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Create session file with start date
            filename = os.path.join(
                output_dir, 
                f"meter_readings_session_{self.session_start_date.strftime('%Y%m%d')}.csv"
            )
            
            # Check if file exists to determine if we need to write header
            file_exists = os.path.exists(filename)
            
            self.session_meter_file = open(filename, 'a', newline='', encoding='utf-8')
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
                fieldnames.append(meter_col)
            
            self.session_meter_writer = csv.DictWriter(self.session_meter_file, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                self.session_meter_writer.writeheader()
            
            print(f"📁 Using session meter file: {filename}")
        
        return self.session_meter_writer
    
    def save_meter_data_to_session_csv(self, meter_data, output_dir):
        """Save meter data to session CSV file (appends throughout session)"""
        if not meter_data["devices"]:
            print("⚠️  No meter data to save")
            return None
        
        # Get the session CSV writer
        writer = self.get_session_meter_file(output_dir)
        
        # Prepare wide format CSV data (one row per collection)
        smile_data = meter_data["devices"].get("smile", {})
        
        if smile_data and writer and self.session_meter_file:
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
            
            # Write data to CSV
            try:
                writer.writerow(row_data)
                self.session_meter_file.flush()  # Ensure data is written
                print(f"✅ Appended meter readings to session file")
                return self.session_meter_file.name
            except Exception as e:
                print(f"❌ Error writing to session file: {e}")
                return None
        
        return None
    
    def finalize_session_meter_file(self, output_dir):
        """Rename session meter file with end date when session ends"""
        if self.session_start_date:
            # Get the end date (today)
            end_date = date.today()
            
            # Generate filenames
            session_filename = os.path.join(
                output_dir, 
                f"meter_readings_session_{self.session_start_date.strftime('%Y%m%d')}.csv"
            )
            final_filename = os.path.join(
                output_dir, 
                f"meter_readings_{self.session_start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            )
            
            # Close the session file if it's open
            if self.session_meter_file:
                self.session_meter_file.close()
                self.session_meter_file = None
            
            # Only rename if the session file exists
            if os.path.exists(session_filename):
                try:
                    os.rename(session_filename, final_filename)
                    print(f"✅ Session meter file finalized: {final_filename}")
                    return final_filename
                except Exception as e:
                    print(f"❌ Error renaming session file: {e}")
                    return session_filename
            else:
                print("ℹ️  No session meter file to finalize")
        
        return None
    
    def should_collect_meter_data_today(self):
        """Check if meter data should be collected today (once per day)"""
        today = date.today()
        
        # If we haven't collected meter data today yet, or if it's a new day
        if self.last_meter_collection_date != today:
            self.last_meter_collection_date = today
            return True
        
        return False
    
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
    
    def get_daily_csv_file(self, output_dir):
        """Get or create daily CSV file for current date"""
        today = date.today()
        
        # Check if we need to start a new file
        if self.current_date != today or self.current_csv_file is None:
            # Close previous file if it exists
            if self.current_csv_file:
                self.current_csv_file.close()
            
            # Create new file for today
            filename = os.path.join(output_dir, f"power_usage_{today.strftime('%Y%m%d')}.csv")
            
            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Check if file exists to determine if we need to write header
            file_exists = os.path.exists(filename)
            
            self.current_csv_file = open(filename, 'a', newline='', encoding='utf-8')
            fieldnames = ['timestamp', 'device', 'appliance', 'power_watts', 'measurement_timestamp', 'module_id', 'meter_id', 'tariff', 'peak_watts', 'offpeak_watts']
            self.current_csv_writer = csv.DictWriter(self.current_csv_file, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                self.current_csv_writer.writeheader()
            
            self.current_date = today
            print(f"📁 Using daily file: {filename}")
        
        return self.current_csv_writer
    
    def save_to_daily_csv(self, power_data, output_dir):
        """Save power data to daily CSV file"""
        if not power_data["devices"]:
            print("⚠️  No power data to save")
            return None
        
        # Get the daily CSV writer
        writer = self.get_daily_csv_file(output_dir)
        
        # Prepare CSV data
        csv_data = []
        for device_name, device_data in power_data["devices"].items():
            if isinstance(device_data, dict) and device_data:
                if device_name == "smile":
                    # Handle Smile device data structure
                    if 'current_power' in device_data:
                        current_power = device_data['current_power']
                        csv_data.append({
                            'timestamp': power_data["timestamp"],
                            'device': device_name,
                            'appliance': 'main_meter',
                            'power_watts': current_power.get('total_watts', 0),
                            'measurement_timestamp': current_power.get('timestamp', ''),
                            'module_id': 'smile_main',
                            'meter_id': 'smile_meter',
                            'tariff': current_power.get('active_tariff', ''),
                            'peak_watts': current_power.get('peak_watts', 0),
                            'offpeak_watts': current_power.get('offpeak_watts', 0)
                        })
                else:
                    # Handle Stretch device data structure
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
        
        # Write data to CSV
        if csv_data and writer:
            writer.writerows(csv_data)
            print(f"✅ Saved {len(csv_data)} measurements to daily CSV")
            return self.current_csv_file.name if self.current_csv_file else None
        
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
                
                if device_name == "smile":
                    # Handle Smile device display
                    if 'current_power' in device_data:
                        current_power = device_data['current_power']
                        power = current_power.get('total_watts', 0)
                        device_total = power
                        tariff = current_power.get('active_tariff', 'unknown')
                        print(f"  {'Main Meter':25} : {power:8.2f} W ({tariff})")
                        
                        # Show meter data if available
                        if 'meter_data' in device_data:
                            meter = device_data['meter_data']
                            if 'net_consumption' in meter:
                                print(f"  {'Net Consumption':25} : {meter['net_consumption']:8.2f} kWh")
                            if 'gas' in meter:
                                print(f"  {'Gas Usage':25} : {meter['gas']:8.2f} m³")
                else:
                    # Handle Stretch device display
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
    
    def run_single_collection(self, output_dir=None, finalize_session=False):
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
                self.save_to_daily_csv(power_data, output_dir)
            
            # Also collect and save meter data (if enabled and it's a new day)
            if self.collect_meter_data and self.should_collect_meter_data_today():
                meter_data = self.collect_daily_meter_data()
                if meter_data["devices"]:
                    self.print_meter_summary(meter_data)
                    if output_dir:
                        self.save_meter_data_to_session_csv(meter_data, output_dir)
            
            # Only finalize session file if explicitly requested (for single runs)
            if finalize_session and output_dir and self.collect_meter_data:
                self.finalize_session_meter_file(output_dir)
            
            return power_data
        else:
            print("❌ No power data collected")
            return None
    
    def run_continuous_collection(self, interval, output_dir=None):
        """Run continuous data collection with daily file rotation"""
        print(f"🔄 Starting continuous collection (interval: {interval}s)")
        print("📅 Power data will be saved to daily CSV files (00:00-23:59)")
        print("📊 Meter data will be collected once per day and saved to session files")
        print("Press Ctrl+C to stop gracefully")
        print("=" * 50)
        
        try:
            while not self.shutdown_requested:
                self.run_single_collection(output_dir)
                print(f"⏰ Waiting {interval} seconds until next collection...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Graceful shutdown requested...")
            self.shutdown_requested = True
        except Exception as e:
            print(f"\n❌ Collection error: {e}")
            # Don't set shutdown flag for regular errors, just log them
        finally:
            # Graceful shutdown cleanup
            self.cleanup_on_shutdown(output_dir)
    
    def cleanup_on_shutdown(self, output_dir=None):
        """Clean up resources on shutdown"""
        print("🧹 Performing cleanup...")
        
        # Close the current power CSV file
        if self.current_csv_file:
            try:
                self.current_csv_file.close()
                print("✅ Closed power usage CSV file")
            except Exception as e:
                print(f"⚠️  Error closing power CSV file: {e}")
        
        # Finalize session meter file
        if output_dir and self.collect_meter_data:
            self.finalize_session_meter_file(output_dir)
        
        print("✅ Cleanup completed")

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
    parser.add_argument("--no-meter", action="store_true",
                       help="Skip meter data collection (power data only)")
    
    args = parser.parse_args()
    
    # Create collector
    collector = PlugwiseCollector(args.config)
    
    # Store meter collection preference
    collector.collect_meter_data = not args.no_meter
    
    # Run collection
    if args.continuous:
        collector.run_continuous_collection(args.interval, args.output)
    else:
        collector.run_single_collection(args.output, finalize_session=True)

if __name__ == "__main__":
    main() 