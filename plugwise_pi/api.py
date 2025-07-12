"""
REST API server for Plugwise Pi.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import get_config
from .database import db_manager
from .utils import setup_logging, create_directories

logger = logging.getLogger(__name__)

# Pydantic models for API responses
class DeviceResponse(BaseModel):
    id: int
    name: str
    mac_address: str
    device_type: str
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ReadingResponse(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    power_watts: Optional[float] = None
    energy_kwh: Optional[float] = None
    temperature_celsius: Optional[float] = None
    humidity_percent: Optional[float] = None
    battery_percent: Optional[float] = None
    is_online: bool

class AlertResponse(BaseModel):
    id: int
    device_id: int
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    is_resolved: bool
    resolved_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    uptime: str


class PlugwiseAPI:
    """REST API server for Plugwise Pi."""
    
    def __init__(self):
        self.config = get_config()
        self.app = FastAPI(
            title="Plugwise Pi API",
            description="API for Plugwise domotics data collection",
            version="0.1.0"
        )
        self.start_time = datetime.utcnow()
        self._setup()
    
    def _setup(self):
        """Setup the API server."""
        setup_logging(self.config)
        create_directories()
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
        logger.info("Plugwise API initialized")
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_model=dict)
        async def root():
            """Root endpoint."""
            return {
                "message": "Plugwise Pi API",
                "version": "0.1.0",
                "docs": "/docs"
            }
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            """Health check endpoint."""
            uptime = datetime.utcnow() - self.start_time
            return HealthResponse(
                status="healthy",
                timestamp=datetime.utcnow(),
                version="0.1.0",
                uptime=str(uptime)
            )
        
        @self.app.get("/devices", response_model=List[DeviceResponse])
        async def get_devices():
            """Get all devices."""
            devices = db_manager.get_all_devices()
            return [DeviceResponse.from_orm(device) for device in devices]
        
        @self.app.get("/devices/{device_id}", response_model=DeviceResponse)
        async def get_device(device_id: int):
            """Get a specific device."""
            device = db_manager.get_device(device_id)
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            return DeviceResponse.from_orm(device)
        
        @self.app.get("/devices/{device_id}/readings", response_model=List[ReadingResponse])
        async def get_device_readings(
            device_id: int,
            limit: int = 100,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None
        ):
            """Get readings for a device."""
            device = db_manager.get_device(device_id)
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            
            readings = db_manager.get_readings(
                device_id=device_id,
                limit=limit,
                start_time=start_time,
                end_time=end_time
            )
            return [ReadingResponse.from_orm(reading) for reading in readings]
        
        @self.app.get("/devices/{device_id}/readings/latest", response_model=ReadingResponse)
        async def get_latest_reading(device_id: int):
            """Get the latest reading for a device."""
            device = db_manager.get_device(device_id)
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            
            reading = db_manager.get_latest_reading(device_id)
            if not reading:
                raise HTTPException(status_code=404, detail="No readings found")
            
            return ReadingResponse.from_orm(reading)
        
        @self.app.get("/alerts", response_model=List[AlertResponse])
        async def get_alerts(device_id: Optional[int] = None):
            """Get active alerts."""
            alerts = db_manager.get_active_alerts(device_id=device_id)
            return [AlertResponse.from_orm(alert) for alert in alerts]
        
        @self.app.post("/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: int):
            """Resolve an alert."""
            try:
                db_manager.resolve_alert(alert_id)
                return {"message": "Alert resolved successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stats")
        async def get_stats():
            """Get system statistics."""
            # TODO: Implement statistics endpoint
            return {
                "total_devices": len(db_manager.get_all_devices()),
                "active_alerts": len(db_manager.get_active_alerts()),
                "uptime": str(datetime.utcnow() - self.start_time)
            }
    
    def run(self):
        """Run the API server."""
        import uvicorn
        
        logger.info(f"Starting API server on {self.config.api.host}:{self.config.api.port}")
        uvicorn.run(
            self.app,
            host=self.config.api.host,
            port=self.config.api.port,
            log_level=self.config.logging.level.lower()
        )


def main():
    """Main entry point for the API server."""
    api = PlugwiseAPI()
    api.run()


if __name__ == "__main__":
    main() 