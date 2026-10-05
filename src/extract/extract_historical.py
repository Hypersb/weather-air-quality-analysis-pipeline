"""
Historical weather data extraction module.

Fetches historical hourly weather data from the Open-Meteo Archive API
for all configured locations and stores the untouched API responses
as raw JSON files.
"""

import json
from datetime import datetime
from pathlib import Path

import requests

from src.config.locations import LOCATIONS


# Open-Meteo Historical Weather API
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_HISTORICAL_DIR = PROJECT_ROOT / "data" / "raw" / "weather" / "historical"


# Historical period for the initial project dataset
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"


# Keep these variables aligned with our regular weather extraction
HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "surface_pressure",
    "cloud_cover",
    "weather_code",
]


def fetch_historical_weather(
    latitude,
    longitude,
    start_date,
    end_date,
):
    """
    Fetch historical hourly weather data from Open-Meteo.

    Args:
        latitude (float): Location latitude.
        longitude (float): Location longitude.
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.

    Returns:
        dict: Raw JSON response from Open-Meteo.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": HOURLY_VARIABLES,
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def save_historical_weather(
    data,
    city_name,
    start_date,
    end_date,
    run_timestamp,
):
    """
    Save raw historical weather data as JSON.
    """

    RAW_HISTORICAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_city_name = city_name.lower().replace(" ", "_")

    filename = (
        f"{safe_city_name}_"
        f"{start_date}_to_{end_date}_"
        f"{run_timestamp}.json"
    )

    file_path = RAW_HISTORICAL_DIR / filename

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


def extract_all_historical_weather():
    """
    Extract historical weather data for every configured location.
    """

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    successful = []
    failed = []

    print("=" * 65)
    print("HISTORICAL WEATHER DATA EXTRACTION")
    print("=" * 65)

    print(f"Start date: {START_DATE}")
    print(f"End date:   {END_DATE}")
    print(f"Locations:  {len(LOCATIONS)}")

    for city_name, coordinates in LOCATIONS.items():

        print(f"\nExtracting historical weather for {city_name}...")

        try:
            historical_data = fetch_historical_weather(
                coordinates["latitude"],
                coordinates["longitude"],
                START_DATE,
                END_DATE,
            )

            file_path = save_historical_weather(
                historical_data,
                city_name,
                START_DATE,
                END_DATE,
                run_timestamp,
            )

            record_count = len(
                historical_data.get("hourly", {}).get("time", [])
            )

            successful.append(city_name)

            print("Success")
            print(f"Hourly records: {record_count:,}")
            print(f"Saved: {file_path}")

        except requests.RequestException as error:
            failed.append(city_name)

            print("Failed")
            print(f"Reason: {error}")

    print("\n" + "=" * 65)
    print("HISTORICAL EXTRACTION SUMMARY")
    print("=" * 65)

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

    print("=" * 65)


if __name__ == "__main__":
    extract_all_historical_weather()