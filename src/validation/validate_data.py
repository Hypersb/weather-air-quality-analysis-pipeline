"""
Data validation module.

Validates the processed Weather & Air Quality dataset before it is
loaded into PostgreSQL.

This module reports data-quality problems without modifying the dataset.
"""

from pathlib import Path

import pandas as pd

from src.config.locations import LOCATIONS


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "weather_air_quality_2025.csv"
)


# ---------------------------------------------------------------------
# Dataset expectations
# ---------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "city",
    "timestamp",
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "surface_pressure",
    "cloud_cover",
    "weather_code",
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "us_aqi",
    "date",
    "year",
    "month",
    "day",
    "hour",
    "day_of_week",
]

NON_NEGATIVE_COLUMNS = [
    "precipitation",
    "wind_speed_10m",
    "pm2_5",
    "pm10",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "us_aqi",
]


# ---------------------------------------------------------------------
# Load dataset
# ---------------------------------------------------------------------

def load_processed_data():
    """
    Load the processed dataset and parse timestamps.
    """

    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found:\n{PROCESSED_FILE}"
        )

    dataframe = pd.read_csv(
        PROCESSED_FILE
    )

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"],
        errors="coerce",
    )

    return dataframe


# ---------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------

def validate_required_columns(dataframe):
    """
    Check that every required column exists.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        print(
            f"[FAIL] Missing required columns: "
            f"{missing_columns}"
        )
        return False

    print("[PASS] All required columns exist.")

    return True


def validate_cities(dataframe):
    """
    Check that all configured cities exist in the dataset.
    """

    expected_cities = set(
        LOCATIONS.keys()
    )

    actual_cities = set(
        dataframe["city"]
        .dropna()
        .unique()
    )

    missing_cities = (
        expected_cities - actual_cities
    )

    unexpected_cities = (
        actual_cities - expected_cities
    )

    if missing_cities:
        print(
            f"[FAIL] Missing cities: "
            f"{sorted(missing_cities)}"
        )
        return False

    if unexpected_cities:
        print(
            f"[FAIL] Unexpected cities: "
            f"{sorted(unexpected_cities)}"
        )
        return False

    print(
        f"[PASS] All {len(expected_cities)} "
        f"configured cities are present."
    )

    return True


def validate_unique_keys(dataframe):
    """
    Ensure city + timestamp uniquely identifies each observation.
    """

    duplicate_count = dataframe.duplicated(
        subset=[
            "city",
            "timestamp",
        ],
        keep=False,
    ).sum()

    if duplicate_count > 0:
        print(
            f"[FAIL] Duplicate city/timestamp rows: "
            f"{duplicate_count:,}"
        )
        return False

    print(
        "[PASS] city + timestamp keys are unique."
    )

    return True


def validate_timestamps(dataframe):
    """
    Check for invalid timestamps.
    """

    invalid_count = (
        dataframe["timestamp"]
        .isna()
        .sum()
    )

    if invalid_count > 0:
        print(
            f"[FAIL] Invalid timestamps: "
            f"{invalid_count:,}"
        )
        return False

    print("[PASS] All timestamps are valid.")

    return True


def validate_date_range(dataframe):
    """
    Check that the dataset covers the expected 2025 period.
    """

    expected_start = pd.Timestamp(
        "2025-01-01 00:00:00"
    )

    expected_end = pd.Timestamp(
        "2025-12-31 23:00:00"
    )

    actual_start = dataframe[
        "timestamp"
    ].min()

    actual_end = dataframe[
        "timestamp"
    ].max()

    print(
        f"       Dataset start: {actual_start}"
    )

    print(
        f"       Dataset end:   {actual_end}"
    )

    if (
        actual_start != expected_start
        or actual_end != expected_end
    ):
        print(
            "[FAIL] Dataset does not cover "
            "the complete expected 2025 period."
        )
        return False

    print(
        "[PASS] Dataset covers the complete "
        "2025 hourly period."
    )

    return True


def validate_humidity(dataframe):
    """
    Ensure relative humidity is between 0 and 100 percent.
    """

    invalid_rows = dataframe[
        (
            dataframe[
                "relative_humidity_2m"
            ] < 0
        )
        |
        (
            dataframe[
                "relative_humidity_2m"
            ] > 100
        )
    ]

    if not invalid_rows.empty:
        print(
            f"[FAIL] Invalid humidity rows: "
            f"{len(invalid_rows):,}"
        )
        return False

    print(
        "[PASS] Relative humidity values "
        "are within 0-100."
    )

    return True


def validate_cloud_cover(dataframe):
    """
    Ensure cloud cover is between 0 and 100 percent.
    """

    invalid_rows = dataframe[
        (
            dataframe[
                "cloud_cover"
            ] < 0
        )
        |
        (
            dataframe[
                "cloud_cover"
            ] > 100
        )
    ]

    if not invalid_rows.empty:
        print(
            f"[FAIL] Invalid cloud-cover rows: "
            f"{len(invalid_rows):,}"
        )
        return False

    print(
        "[PASS] Cloud-cover values "
        "are within 0-100."
    )

    return True


def validate_non_negative_values(dataframe):
    """
    Ensure selected measurements do not contain negative values.
    """

    passed = True

    for column in NON_NEGATIVE_COLUMNS:

        invalid_count = (
            dataframe[column] < 0
        ).sum()

        if invalid_count > 0:

            print(
                f"[FAIL] {column} contains "
                f"{invalid_count:,} negative values."
            )

            passed = False

        else:

            print(
                f"[PASS] {column} contains "
                "no negative values."
            )

    return passed


def report_missing_values(dataframe):
    """
    Report missing values by column.

    Missing values are reported rather than automatically removed
    because null values may legitimately originate from the source API.
    """

    print("\nMissing values by column:")

    missing_values = (
        dataframe
        .isna()
        .sum()
        .sort_values(
            ascending=False
        )
    )

    columns_with_missing = (
        missing_values[
            missing_values > 0
        ]
    )

    if columns_with_missing.empty:

        print("  None")

        return True

    for column, count in (
        columns_with_missing.items()
    ):

        percentage = (
            count / len(dataframe)
        ) * 100

        print(
            f"  {column}: "
            f"{count:,} "
            f"({percentage:.2f}%)"
        )

    print(
        "[WARNING] Missing values detected. "
        "Review before database loading."
    )

    return True


def report_rows_by_city(dataframe):
    """
    Display observation counts for each city.
    """

    print("\nRows by city:")

    counts = (
        dataframe
        .groupby("city")
        .size()
        .sort_index()
    )

    for city, count in counts.items():

        print(
            f"  {city}: "
            f"{count:,}"
        )


# ---------------------------------------------------------------------
# Validation pipeline
# ---------------------------------------------------------------------

def validate_dataset():
    """
    Run all validation checks.

    Returns:
        bool: True if all critical checks pass.
    """

    print("=" * 65)
    print("DATA QUALITY VALIDATION")
    print("=" * 65)

    dataframe = load_processed_data()

    print(
        f"\nDataset rows: "
        f"{len(dataframe):,}"
    )

    print(
        f"Dataset columns: "
        f"{len(dataframe.columns)}"
    )

    print()

    validation_results = []

    validation_results.append(
        validate_required_columns(
            dataframe
        )
    )

    # Stop here if schema is wrong because later checks
    # depend on these columns.
    if not validation_results[-1]:

        print("\nValidation stopped because required columns are missing.")
        return False

    validation_results.extend(
        [
            validate_cities(
                dataframe
            ),
            validate_unique_keys(
                dataframe
            ),
            validate_timestamps(
                dataframe
            ),
            validate_date_range(
                dataframe
            ),
            validate_humidity(
                dataframe
            ),
            validate_cloud_cover(
                dataframe
            ),
            validate_non_negative_values(
                dataframe
            ),
        ]
    )

    report_missing_values(
        dataframe
    )

    report_rows_by_city(
        dataframe
    )

    passed = all(
        validation_results
    )

    print("\n" + "=" * 65)

    if passed:

        print(
            "VALIDATION RESULT: PASS"
        )

        print(
            "Dataset passed all critical "
            "quality checks."
        )

    else:

        print(
            "VALIDATION RESULT: FAIL"
        )

        print(
            "One or more critical data-quality "
            "checks failed."
        )

    print("=" * 65)

    return passed


if __name__ == "__main__":
    validate_dataset()