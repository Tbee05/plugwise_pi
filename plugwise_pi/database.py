"""
Database operations for Plugwise Pi.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from .models import Base, Device, Reading, Alert, SystemLog, get_session_factory, create_tables
from .config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.config = get_config()
        self.SessionLocal = None
        self.engine = None
        self._setup_database()
    
    def _setup_database(self):
        """Setup database connection."""
        db_config = self.config.database
        
        if db_config.type == "sqlite":
            db_path = db_config.sqlite["path"]
            database_url = f"sqlite:///{db_path}"
        elif db_config.type == "postgresql":
            pg_config = db_config.postgresql
            database_url = (
                f"postgresql://{pg_config['user']}:{pg_config['password']}"
                f"@{pg_config['host']}:{pg_config['port']}/{pg_config['name']}"
            )
        else:
            raise ValueError(f"Unsupported database type: {db_config.type}")
        
        self.SessionLocal, self.engine = get_session_factory(database_url)
        create_tables(self.engine)
        logger.info(f"Database initialized: {db_config.type}")
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Close a database session."""
        session.close()
    
    def add_device(self, name: str, mac_address: str, device_type: str = "circle", 
                   location: Optional[str] = None, description: Optional[str] = None) -> Device:
        """Add a new device to the database."""
        session = self.get_session()
        try:
            device = Device(
                name=name,
                mac_address=mac_address,
                device_type=device_type,
                location=location,
                description=description
            )
            session.add(device)
            session.commit()
            session.refresh(device)
            logger.info(f"Added device: {name} ({mac_address})")
            return device
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding device: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_device(self, device_id: int) -> Optional[Device]:
        """Get a device by ID."""
        session = self.get_session()
        try:
            return session.query(Device).filter(Device.id == device_id).first()
        finally:
            self.close_session(session)
    
    def get_device_by_mac(self, mac_address: str) -> Optional[Device]:
        """Get a device by MAC address."""
        session = self.get_session()
        try:
            return session.query(Device).filter(Device.mac_address == mac_address).first()
        finally:
            self.close_session(session)
    
    def get_all_devices(self) -> List[Device]:
        """Get all active devices."""
        session = self.get_session()
        try:
            return session.query(Device).filter(Device.is_active == True).all()
        finally:
            self.close_session(session)
    
    def add_reading(self, device_id: int, power_watts: Optional[float] = None,
                   energy_kwh: Optional[float] = None, temperature_celsius: Optional[float] = None,
                   humidity_percent: Optional[float] = None, battery_percent: Optional[float] = None,
                   is_online: bool = True, raw_data: Optional[str] = None) -> Reading:
        """Add a new reading to the database."""
        session = self.get_session()
        try:
            reading = Reading(
                device_id=device_id,
                power_watts=power_watts,
                energy_kwh=energy_kwh,
                temperature_celsius=temperature_celsius,
                humidity_percent=humidity_percent,
                battery_percent=battery_percent,
                is_online=is_online,
                raw_data=raw_data
            )
            session.add(reading)
            session.commit()
            session.refresh(reading)
            return reading
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding reading: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_readings(self, device_id: int, limit: int = 100, 
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[Reading]:
        """Get readings for a device."""
        session = self.get_session()
        try:
            query = session.query(Reading).filter(Reading.device_id == device_id)
            
            if start_time:
                query = query.filter(Reading.timestamp >= start_time)
            if end_time:
                query = query.filter(Reading.timestamp <= end_time)
            
            return query.order_by(desc(Reading.timestamp)).limit(limit).all()
        finally:
            self.close_session(session)
    
    def get_latest_reading(self, device_id: int) -> Optional[Reading]:
        """Get the latest reading for a device."""
        session = self.get_session()
        try:
            return session.query(Reading).filter(
                Reading.device_id == device_id
            ).order_by(desc(Reading.timestamp)).first()
        finally:
            self.close_session(session)
    
    def add_alert(self, device_id: int, alert_type: str, severity: str, 
                  message: str) -> Alert:
        """Add a new alert to the database."""
        session = self.get_session()
        try:
            alert = Alert(
                device_id=device_id,
                alert_type=alert_type,
                severity=severity,
                message=message
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            logger.info(f"Added alert: {alert_type} - {message}")
            return alert
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding alert: {e}")
            raise
        finally:
            self.close_session(session)
    
    def get_active_alerts(self, device_id: Optional[int] = None) -> List[Alert]:
        """Get active (unresolved) alerts."""
        session = self.get_session()
        try:
            query = session.query(Alert).filter(Alert.is_resolved == False)
            if device_id:
                query = query.filter(Alert.device_id == device_id)
            return query.order_by(desc(Alert.timestamp)).all()
        finally:
            self.close_session(session)
    
    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved."""
        session = self.get_session()
        try:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.is_resolved = True
                alert.resolved_at = datetime.utcnow()
                session.commit()
                logger.info(f"Resolved alert: {alert_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error resolving alert: {e}")
            raise
        finally:
            self.close_session(session)
    
    def cleanup_old_data(self, days: int = 365):
        """Clean up old data based on retention policy."""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Delete old readings
            deleted_readings = session.query(Reading).filter(
                Reading.timestamp < cutoff_date
            ).delete()
            
            # Delete old system logs
            deleted_logs = session.query(SystemLog).filter(
                SystemLog.timestamp < cutoff_date
            ).delete()
            
            session.commit()
            logger.info(f"Cleaned up {deleted_readings} old readings and {deleted_logs} old logs")
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up old data: {e}")
            raise
        finally:
            self.close_session(session)


# Global database manager instance
db_manager = DatabaseManager() 