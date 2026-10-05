"""
Location configuration for the Weather & Air Quality Data Pipeline.

Each location contains the latitude and longitude used by the
Open-Meteo Weather and Air Quality APIs.

Keeping locations in one configuration file prevents coordinates
from being duplicated across extraction scripts.
"""


LOCATIONS = {
    "Salt Lake City": {
        "latitude": 40.7608,
        "longitude": -111.8910,
    },
    "Denver": {
        "latitude": 39.7392,
        "longitude": -104.9903,
    },
    "Los Angeles": {
        "latitude": 34.0522,
        "longitude": -118.2437,
    },
    "Seattle": {
        "latitude": 47.6062,
        "longitude": -122.3321,
    },
    "Chicago": {
        "latitude": 41.8781,
        "longitude": -87.6298,
    },
    "New York": {
        "latitude": 40.7128,
        "longitude": -74.0060,
    },
    "Houston": {
        "latitude": 29.7604,
        "longitude": -95.3698,
    },
    "Phoenix": {
        "latitude": 33.4484,
        "longitude": -112.0740,
    },
}