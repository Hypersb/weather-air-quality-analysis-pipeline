"""
Air quality data extraction module.

Fetches hourly air quality data from the Open-Meteo Air Quality API
for all configured locations and stores the untouched API responses
as raw JSON files.
"""

import json
from datetime import datetime
from pathlib import Path

import requests

from src.config.locations import LOCATIONS


# Open-Meteo Air Quality API
BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_AIR_QUALITY_DIR = PROJECT_ROOT / "data" / "raw" / "air_quality"


# Air quality variables we want to collect
HOURLY_VARIABLES = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "us_aqi",
]


def fetch_air_quality_data(latitude, longitude):
    """
    Fetch hourly air quality data from Open-Meteo.

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
        "timezone": "auto",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def save_raw_air_quality_data(data, city_name, run_timestamp):
    """
    Save a raw air quality API response as JSON.

    Args:
        data (dict): Raw API response.
        city_name (str): Name of the city.
        run_timestamp (str): Timestamp identifying this extraction run.

    Returns:
        Path: Path of the saved JSON file.
    """

    RAW_AIR_QUALITY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_city_name = city_name.lower().replace(" ", "_")

    filename = f"{safe_city_name}_{run_timestamp}.json"

    file_path = RAW_AIR_QUALITY_DIR / filename

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


def extract_all_air_quality():
    """
    Extract and save air quality data for every configured location.
    """

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    successful = []
    failed = []

    print("=" * 60)
    print("AIR QUALITY DATA EXTRACTION")
    print("=" * 60)

    for city_name, coordinates in LOCATIONS.items():

        print(f"\nExtracting air quality data for {city_name}...")

        try:
            air_quality_data = fetch_air_quality_data(
                coordinates["latitude"],
                coordinates["longitude"],
            )

            file_path = save_raw_air_quality_data(
                air_quality_data,
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
    extract_all_air_quality()