"""
Data models for Plugwise Pi.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Device(Base):
    """Model for Plugwise devices."""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    mac_address = Column(String(17), unique=True, nullable=False)
    device_type = Column(String(50), nullable=False, default="circle")
    location = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Reading(Base):
    """Model for device readings."""
    __tablename__ = "readings"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    power_watts = Column(Float)
    energy_kwh = Column(Float)
    temperature_celsius = Column(Float)
    humidity_percent = Column(Float)
    battery_percent = Column(Float)
    is_online = Column(Boolean, default=True)
    raw_data = Column(Text)  # JSON string of raw device data


class Alert(Base):
    """Model for system alerts."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, nullable=False)
    alert_type = Column(String(50), nullable=False)  # offline, high_power, low_battery, etc.
    severity = Column(String(20), nullable=False)  # info, warning, error, critical
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)


class SystemLog(Base):
    """Model for system logs."""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    module = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(Text)  # JSON string of additional data


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")


def get_session_factory(database_url: str):
    """Create a session factory for database operations."""
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal, engine 