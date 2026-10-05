"""
Weather data extraction module.

Fetches hourly weather data from the Open-Meteo Weather Forecast API
for all configured locations and stores the untouched API responses
as raw JSON files.
"""

import json
from datetime import datetime
from pathlib import Path

import requests

from src.config.locations import LOCATIONS


BASE_URL = "https://api.open-meteo.com/v1/forecast"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_WEATHER_DIR = PROJECT_ROOT / "data" / "raw" / "weather"


HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "surface_pressure",
    "cloud_cover",
    "weather_code",
]


def fetch_weather_data(latitude, longitude):
    """
    Fetch hourly weather data from Open-Meteo.

    Args:
        latitude (float): Location latitude.
        longitude (float): Location longitude.

    Returns:
        dict: Raw JSON response from Open-Meteo.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": HOURLY_VARIABLES,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def save_raw_weather_data(data, city_name, run_timestamp):
    """
    Save a raw weather API response as JSON.

    Args:
        data (dict): Raw API response.
        city_name (str): Name of the city.
        run_timestamp (str): Timestamp identifying this extraction run.

    Returns:
        Path: Path of the saved JSON file.
    """

    RAW_WEATHER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_city_name = city_name.lower().replace(" ", "_")

    filename = f"{safe_city_name}_{run_timestamp}.json"

    file_path = RAW_WEATHER_DIR / filename

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
        )

    return file_path


def extract_all_weather():
    """
    Extract and save weather data for every configured location.
    """

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    successful = []
    failed = []

    print("=" * 60)
    print("WEATHER DATA EXTRACTION")
    print("=" * 60)

    for city_name, coordinates in LOCATIONS.items():

        print(f"\nExtracting weather data for {city_name}...")

        try:
            weather_data = fetch_weather_data(
                coordinates["latitude"],
                coordinates["longitude"],
            )

            file_path = save_raw_weather_data(
                weather_data,
                city_name,
                run_timestamp,
            )

            successful.append(city_name)

            print("Success")
            print(f"Saved: {file_path}")

        except requests.RequestException as error:
            failed.append(city_name)

            print("Failed")
            print(f"Reason: {error}")

    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    print(f"Total locations: {len(LOCATIONS)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print("\nSuccessful locations:")

        for city in successful:
            print(f"  - {city}")

    if failed:
        print("\nFailed locations:")

        for city in failed:
            print(f"  - {city}")

    print("=" * 60)


if __name__ == "__main__":
    extract_all_weather()