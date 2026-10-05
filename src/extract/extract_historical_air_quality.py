"""
Historical air quality data extraction module.

Fetches historical hourly air quality data from the Open-Meteo
Air Quality API for all configured locations and stores the
untouched responses as raw JSON files.
"""

import json
from datetime import datetime
from pathlib import Path

import requests

from src.config.locations import LOCATIONS


BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_HISTORICAL_AIR_QUALITY_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "air_quality"
    / "historical"
)


# Must match our historical weather period
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"


HOURLY_VARIABLES = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "us_aqi",
]


def fetch_historical_air_quality(
    latitude,
    longitude,
    start_date,
    end_date,
):
    """
    Fetch historical hourly air quality data.

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
        "timezone": "auto",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def save_historical_air_quality(
    data,
    city_name,
    start_date,
    end_date,
    run_timestamp,
):
    """
    Save raw historical air quality data as JSON.
    """

    RAW_HISTORICAL_AIR_QUALITY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_city_name = city_name.lower().replace(" ", "_")

    filename = (
        f"{safe_city_name}_"
        f"{start_date}_to_{end_date}_"
        f"{run_timestamp}.json"
    )

    file_path = (
        RAW_HISTORICAL_AIR_QUALITY_DIR
        / filename
    )

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


def extract_all_historical_air_quality():
    """
    Extract historical air quality data for every configured location.
    """

    run_timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    successful = []
    failed = []

    total_records = 0

    print("=" * 65)
    print("HISTORICAL AIR QUALITY DATA EXTRACTION")
    print("=" * 65)

    print(f"Start date: {START_DATE}")
    print(f"End date:   {END_DATE}")
    print(f"Locations:  {len(LOCATIONS)}")

    for city_name, coordinates in LOCATIONS.items():

        print(
            f"\nExtracting historical air quality "
            f"for {city_name}..."
        )

        try:
            air_quality_data = (
                fetch_historical_air_quality(
                    coordinates["latitude"],
                    coordinates["longitude"],
                    START_DATE,
                    END_DATE,
                )
            )

            file_path = save_historical_air_quality(
                air_quality_data,
                city_name,
                START_DATE,
                END_DATE,
                run_timestamp,
            )

            record_count = len(
                air_quality_data
                .get("hourly", {})
                .get("time", [])
            )

            total_records += record_count
            successful.append(city_name)

            print("Success")
            print(
                f"Hourly records: "
                f"{record_count:,}"
            )
            print(f"Saved: {file_path}")

        except requests.RequestException as error:

            failed.append(city_name)

            print("Failed")
            print(f"Reason: {error}")

    print("\n" + "=" * 65)
    print("HISTORICAL AIR QUALITY SUMMARY")
    print("=" * 65)

    print(
        f"Total locations: "
        f"{len(LOCATIONS)}"
    )

    print(
        f"Successful: "
        f"{len(successful)}"
    )

    print(
        f"Failed: "
        f"{len(failed)}"
    )

    print(
        f"Total hourly records: "
        f"{total_records:,}"
    )

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
    extract_all_historical_air_quality()