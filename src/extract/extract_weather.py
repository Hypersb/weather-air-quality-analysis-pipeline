import json
from datetime import datetime
from pathlib import Path

import requests


BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Raw weather data directory
RAW_WEATHER_DIR = PROJECT_ROOT / "data" / "raw" / "weather"


def fetch_weather_data(latitude, longitude):
    """
    Fetch hourly weather forecast data from Open-Meteo.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "surface_pressure",
            "cloud_cover",
            "weather_code"
        ],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def save_raw_weather_data(data, city_name):
    """
    Save the raw API response as a JSON file.
    """

    RAW_WEATHER_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{city_name.lower().replace(' ', '_')}_{timestamp}.json"

    file_path = RAW_WEATHER_DIR / filename

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    return file_path


if __name__ == "__main__":

    city_name = "Salt Lake City"

    latitude = 40.7608
    longitude = -111.8910

    weather_data = fetch_weather_data(
        latitude,
        longitude
    )

    file_path = save_raw_weather_data(
        weather_data,
        city_name
    )

    print("Weather data fetched successfully.")
    print(f"Raw data saved to: {file_path}")