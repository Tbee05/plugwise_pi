# Plugwise Pi API Documentation

## Overview

The Plugwise Pi API provides RESTful endpoints for accessing data collected from Plugwise domotics devices.

## Base URL

```
http://localhost:8080
```

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Endpoints

### Health Check

#### GET /health

Returns the health status of the API server.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "0.1.0",
  "uptime": "1:23:45"
}
```

### Devices

#### GET /devices

Returns a list of all configured devices.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Living Room Circle",
    "mac_address": "00:01:02:03:04:05",
    "device_type": "circle",
    "location": "Living Room",
    "description": "Main living room power monitoring",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  }
]
```

#### GET /devices/{device_id}

Returns information about a specific device.

**Parameters:**
- `device_id` (integer): The ID of the device

**Response:**
```json
{
  "id": 1,
  "name": "Living Room Circle",
  "mac_address": "00:01:02:03:04:05",
  "device_type": "circle",
  "location": "Living Room",
  "description": "Main living room power monitoring",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Readings

#### GET /devices/{device_id}/readings

Returns readings for a specific device.

**Parameters:**
- `device_id` (integer): The ID of the device
- `limit` (integer, optional): Maximum number of readings to return (default: 100)
- `start_time` (datetime, optional): Start time for filtering readings
- `end_time` (datetime, optional): End time for filtering readings

**Response:**
```json
[
  {
    "id": 1,
    "device_id": 1,
    "timestamp": "2024-01-01T12:00:00Z",
    "power_watts": 150.5,
    "energy_kwh": 0.042,
    "temperature_celsius": 22.5,
    "humidity_percent": 45.2,
    "battery_percent": 95.0,
    "is_online": true
  }
]
```

#### GET /devices/{device_id}/readings/latest

Returns the latest reading for a specific device.

**Parameters:**
- `device_id` (integer): The ID of the device

**Response:**
```json
{
  "id": 1,
  "device_id": 1,
  "timestamp": "2024-01-01T12:00:00Z",
  "power_watts": 150.5,
  "energy_kwh": 0.042,
  "temperature_celsius": 22.5,
  "humidity_percent": 45.2,
  "battery_percent": 95.0,
  "is_online": true
}
```

### Alerts

#### GET /alerts

Returns active alerts.

**Parameters:**
- `device_id` (integer, optional): Filter alerts by device ID

**Response:**
```json
[
  {
    "id": 1,
    "device_id": 1,
    "alert_type": "high_power",
    "severity": "warning",
    "message": "Power consumption is above threshold",
    "timestamp": "2024-01-01T12:00:00Z",
    "is_resolved": false,
    "resolved_at": null
  }
]
```

#### POST /alerts/{alert_id}/resolve

Marks an alert as resolved.

**Parameters:**
- `alert_id` (integer): The ID of the alert to resolve

**Response:**
```json
{
  "message": "Alert resolved successfully"
}
```

### Statistics

#### GET /stats

Returns system statistics.

**Response:**
```json
{
  "total_devices": 3,
  "active_alerts": 1,
  "uptime": "1:23:45"
}
```

## Error Responses

The API returns standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a detail message:

```json
{
  "detail": "Device not found"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. By default:
- 100 requests per minute
- Burst size of 20 requests

## CORS

The API supports CORS for web applications. Configured origins can be set in the configuration file.

## Examples

### Using curl

```bash
# Get all devices
curl http://localhost:8080/devices

# Get latest reading for device 1
curl http://localhost:8080/devices/1/readings/latest

# Get readings for the last hour
curl "http://localhost:8080/devices/1/readings?start_time=2024-01-01T11:00:00Z&end_time=2024-01-01T12:00:00Z"

# Resolve an alert
curl -X POST http://localhost:8080/alerts/1/resolve
```

### Using Python requests

```python
import requests

# Get all devices
response = requests.get('http://localhost:8080/devices')
devices = response.json()

# Get latest reading
response = requests.get('http://localhost:8080/devices/1/readings/latest')
reading = response.json()

# Resolve alert
response = requests.post('http://localhost:8080/alerts/1/resolve')
```

## Interactive Documentation

The API provides interactive documentation at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running. 