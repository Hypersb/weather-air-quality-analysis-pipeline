"""
Historical data transformation module.

Reads historical weather and air-quality JSON files, converts the
hourly arrays into tabular data, combines all configured cities,
merges weather and air-quality observations by city and timestamp,
performs basic cleaning, and saves the resulting dataset as CSV.
"""

import json
from pathlib import Path

import pandas as pd

from src.config.locations import LOCATIONS


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

HISTORICAL_WEATHER_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "weather"
    / "historical"
)

HISTORICAL_AIR_QUALITY_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "air_quality"
    / "historical"
)

PROCESSED_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

OUTPUT_FILE = (
    PROCESSED_DATA_DIR
    / "weather_air_quality_2025.csv"
)


# ---------------------------------------------------------------------
# Expected columns
# ---------------------------------------------------------------------

WEATHER_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "surface_pressure",
    "cloud_cover",
    "weather_code",
]

AIR_QUALITY_COLUMNS = [
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "us_aqi",
]


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def normalize_city_name(city_name):
    """
    Convert a city name into the filename format used by extraction.

    Example:
        Salt Lake City -> salt_lake_city
    """

    return city_name.lower().replace(" ", "_")


def find_latest_file(directory, city_name):
    """
    Find the most recently modified historical JSON file for a city.

    Args:
        directory (Path): Directory containing historical JSON files.
        city_name (str): Human-readable city name.

    Returns:
        Path: Latest matching JSON file.

    Raises:
        FileNotFoundError: If no matching file exists.
    """

    safe_city_name = normalize_city_name(city_name)

    matching_files = list(
        directory.glob(
            f"{safe_city_name}_*.json"
        )
    )

    if not matching_files:
        raise FileNotFoundError(
            f"No historical file found for {city_name} "
            f"in {directory}"
        )

    return max(
        matching_files,
        key=lambda file_path: file_path.stat().st_mtime,
    )


def load_json(file_path):
    """
    Load a JSON file and return it as a Python dictionary.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def hourly_json_to_dataframe(data, city_name, expected_columns):
    """
    Convert Open-Meteo hourly JSON data into a Pandas DataFrame.

    Args:
        data (dict): Raw Open-Meteo API response.
        city_name (str): City represented by the response.
        expected_columns (list): Variables expected in hourly data.

    Returns:
        pandas.DataFrame: Tabular hourly dataset.

    Raises:
        ValueError: If required hourly data is missing.
    """

    if "hourly" not in data:
        raise ValueError(
            f"Missing 'hourly' section for {city_name}"
        )

    hourly = data["hourly"]

    if "time" not in hourly:
        raise ValueError(
            f"Missing hourly timestamps for {city_name}"
        )

    missing_columns = [
        column
        for column in expected_columns
        if column not in hourly
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns for {city_name}: "
            f"{missing_columns}"
        )

    dataframe_data = {
        "timestamp": hourly["time"],
    }

    for column in expected_columns:
        dataframe_data[column] = hourly[column]

    dataframe = pd.DataFrame(dataframe_data)

    dataframe.insert(
        0,
        "city",
        city_name,
    )

    return dataframe


# ---------------------------------------------------------------------
# Weather transformation
# ---------------------------------------------------------------------

def transform_weather():
    """
    Transform historical weather files for all configured cities.

    Returns:
        pandas.DataFrame: Combined historical weather dataset.
    """

    city_dataframes = []

    print("\nTransforming historical weather data...")

    for city_name in LOCATIONS:

        weather_file = find_latest_file(
            HISTORICAL_WEATHER_DIR,
            city_name,
        )

        weather_json = load_json(
            weather_file
        )

        weather_dataframe = hourly_json_to_dataframe(
            weather_json,
            city_name,
            WEATHER_COLUMNS,
        )

        city_dataframes.append(
            weather_dataframe
        )

        print(
            f"  {city_name}: "
            f"{len(weather_dataframe):,} rows"
        )

    weather_dataframe = pd.concat(
        city_dataframes,
        ignore_index=True,
    )

    return weather_dataframe


# ---------------------------------------------------------------------
# Air-quality transformation
# ---------------------------------------------------------------------

def transform_air_quality():
    """
    Transform historical air-quality files for all configured cities.

    Returns:
        pandas.DataFrame: Combined historical air-quality dataset.
    """

    city_dataframes = []

    print("\nTransforming historical air quality data...")

    for city_name in LOCATIONS:

        air_quality_file = find_latest_file(
            HISTORICAL_AIR_QUALITY_DIR,
            city_name,
        )

        air_quality_json = load_json(
            air_quality_file
        )

        air_quality_dataframe = hourly_json_to_dataframe(
            air_quality_json,
            city_name,
            AIR_QUALITY_COLUMNS,
        )

        city_dataframes.append(
            air_quality_dataframe
        )

        print(
            f"  {city_name}: "
            f"{len(air_quality_dataframe):,} rows"
        )

    air_quality_dataframe = pd.concat(
        city_dataframes,
        ignore_index=True,
    )

    return air_quality_dataframe


# ---------------------------------------------------------------------
# Dataset merge
# ---------------------------------------------------------------------

def merge_datasets(
    weather_dataframe,
    air_quality_dataframe,
):
    """
    Merge weather and air-quality datasets by city and timestamp.
    """

    weather_dataframe["timestamp"] = pd.to_datetime(
        weather_dataframe["timestamp"],
        errors="coerce",
    )

    air_quality_dataframe["timestamp"] = pd.to_datetime(
        air_quality_dataframe["timestamp"],
        errors="coerce",
    )

    merged_dataframe = pd.merge(
        weather_dataframe,
        air_quality_dataframe,
        on=[
            "city",
            "timestamp",
        ],
        how="inner",
        validate="one_to_one",
    )

    return merged_dataframe


# ---------------------------------------------------------------------
# Basic cleaning and feature creation
# ---------------------------------------------------------------------

def clean_dataset(dataframe):
    """
    Perform basic cleaning and create useful time-based features.
    """

    dataframe = dataframe.copy()

    # Remove rows where timestamp conversion failed
    dataframe = dataframe.dropna(
        subset=["timestamp"]
    )

    # Remove exact duplicate rows
    dataframe = dataframe.drop_duplicates()

    # Sort observations consistently
    dataframe = dataframe.sort_values(
        by=[
            "city",
            "timestamp",
        ]
    )

    # Reset DataFrame index
    dataframe = dataframe.reset_index(
        drop=True
    )

    # Create useful analytical time features
    dataframe["date"] = (
        dataframe["timestamp"].dt.date
    )

    dataframe["year"] = (
        dataframe["timestamp"].dt.year
    )

    dataframe["month"] = (
        dataframe["timestamp"].dt.month
    )

    dataframe["day"] = (
        dataframe["timestamp"].dt.day
    )

    dataframe["hour"] = (
        dataframe["timestamp"].dt.hour
    )

    dataframe["day_of_week"] = (
        dataframe["timestamp"].dt.day_name()
    )

    return dataframe


# ---------------------------------------------------------------------
# Validation summary
# ---------------------------------------------------------------------

def print_data_summary(dataframe):
    """
    Print a basic summary of the transformed dataset.
    """

    print("\n" + "=" * 65)
    print("TRANSFORMED DATA SUMMARY")
    print("=" * 65)

    print(
        f"Rows: "
        f"{len(dataframe):,}"
    )

    print(
        f"Columns: "
        f"{len(dataframe.columns)}"
    )

    print(
        f"Cities: "
        f"{dataframe['city'].nunique()}"
    )

    print(
        f"Start timestamp: "
        f"{dataframe['timestamp'].min()}"
    )

    print(
        f"End timestamp: "
        f"{dataframe['timestamp'].max()}"
    )

    duplicate_keys = dataframe.duplicated(
        subset=[
            "city",
            "timestamp",
        ]
    ).sum()

    print(
        f"Duplicate city/timestamp keys: "
        f"{duplicate_keys:,}"
    )

    print(
        f"Total missing values: "
        f"{dataframe.isna().sum().sum():,}"
    )

    print("\nRows by city:")

    city_counts = (
        dataframe
        .groupby("city")
        .size()
        .sort_index()
    )

    for city, count in city_counts.items():
        print(
            f"  {city}: "
            f"{count:,}"
        )

    print("=" * 65)


# ---------------------------------------------------------------------
# Save processed dataset
# ---------------------------------------------------------------------

def save_processed_data(dataframe):
    """
    Save the transformed dataset as CSV.
    """

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    return OUTPUT_FILE


# ---------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------

def transform_historical_data():
    """
    Run the complete historical transformation pipeline.
    """

    print("=" * 65)
    print("HISTORICAL DATA TRANSFORMATION")
    print("=" * 65)

    weather_dataframe = transform_weather()

    print(
        f"\nCombined weather rows: "
        f"{len(weather_dataframe):,}"
    )

    air_quality_dataframe = transform_air_quality()

    print(
        f"\nCombined air quality rows: "
        f"{len(air_quality_dataframe):,}"
    )

    print("\nMerging weather and air quality data...")

    merged_dataframe = merge_datasets(
        weather_dataframe,
        air_quality_dataframe,
    )

    print(
        f"Merged rows: "
        f"{len(merged_dataframe):,}"
    )

    print("\nCleaning merged dataset...")

    cleaned_dataframe = clean_dataset(
        merged_dataframe
    )

    print_data_summary(
        cleaned_dataframe
    )

    output_file = save_processed_data(
        cleaned_dataframe
    )

    print("\nTransformation completed successfully.")
    print(
        f"Processed dataset saved to:\n"
        f"{output_file}"
    )

    return cleaned_dataframe


if __name__ == "__main__":
    transform_historical_data()