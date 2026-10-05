"""
PostgreSQL data loader.

Loads the validated historical weather and air-quality dataset
into the PostgreSQL analytics database.
"""

import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values


# ---------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "weather_air_quality_2025.csv"
)

ENV_FILE = PROJECT_ROOT / ".env"

TABLE_NAME = "weather_air_quality"


# Columns loaded from the processed dataset.
# PostgreSQL generates the id column automatically.
LOAD_COLUMNS = [
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


# ---------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------

def load_database_config():
    """
    Load PostgreSQL connection settings from the local .env file.
    """

    load_dotenv(ENV_FILE)

    config = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }

    missing_values = [
        key
        for key, value in config.items()
        if not value
    ]

    if missing_values:
        raise ValueError(
            "Missing database environment variables: "
            + ", ".join(missing_values)
        )

    return config


# ---------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------

def load_processed_dataset():
    """
    Read the validated processed CSV.
    """

    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found:\n{PROCESSED_FILE}"
        )

    dataframe = pd.read_csv(
        PROCESSED_FILE,
        parse_dates=["timestamp", "date"],
    )

    missing_columns = [
        column
        for column in LOAD_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset is missing columns: {missing_columns}"
        )

    return dataframe[LOAD_COLUMNS]


# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------

def connect_to_database():
    """
    Create and return a PostgreSQL connection.
    """

    config = load_database_config()

    connection = psycopg2.connect(
        **config
    )

    return connection


# ---------------------------------------------------------------------
# Database checks
# ---------------------------------------------------------------------

def verify_table_exists(connection):
    """
    Confirm that the destination table exists.
    """

    query = """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
        );
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (TABLE_NAME,),
        )

        exists = cursor.fetchone()[0]

    if not exists:
        raise RuntimeError(
            f"PostgreSQL table '{TABLE_NAME}' does not exist. "
            "Run sql/schema/create_tables.sql first."
        )


def get_database_row_count(connection):
    """
    Return the number of rows currently stored in the table.
    """

    query = f"""
        SELECT COUNT(*)
        FROM {TABLE_NAME};
    """

    with connection.cursor() as cursor:
        cursor.execute(query)

        count = cursor.fetchone()[0]

    return count


# ---------------------------------------------------------------------
# Data insertion
# ---------------------------------------------------------------------

def prepare_rows(dataframe):
    """
    Convert DataFrame rows into tuples suitable for PostgreSQL.
    """

    prepared_dataframe = dataframe.copy()

    # Convert pandas timestamp objects into native Python objects.
    prepared_dataframe["timestamp"] = (
        prepared_dataframe["timestamp"]
        .dt.to_pydatetime()
    )

    prepared_dataframe["date"] = (
        prepared_dataframe["date"]
        .dt.date
    )

    # Convert any pandas NaN values to Python None.
    prepared_dataframe = prepared_dataframe.astype(
        object
    ).where(
        pd.notnull(prepared_dataframe),
        None,
    )

    return list(
        prepared_dataframe.itertuples(
            index=False,
            name=None,
        )
    )


def insert_dataset(connection, dataframe):
    """
    Insert the processed dataset into PostgreSQL.

    ON CONFLICT makes the load idempotent. If the same city/timestamp
    already exists, PostgreSQL skips that row rather than creating a
    duplicate observation.
    """

    columns_sql = ", ".join(
        LOAD_COLUMNS
    )

    query = f"""
        INSERT INTO {TABLE_NAME} (
            {columns_sql}
        )
        VALUES %s
        ON CONFLICT (city, timestamp)
        DO NOTHING;
    """

    rows = prepare_rows(
        dataframe
    )

    before_count = get_database_row_count(
        connection
    )

    with connection.cursor() as cursor:
        execute_values(
            cursor,
            query,
            rows,
            page_size=1000,
        )

    connection.commit()

    after_count = get_database_row_count(
        connection
    )

    inserted_count = (
        after_count - before_count
    )

    return inserted_count


# ---------------------------------------------------------------------
# Post-load verification
# ---------------------------------------------------------------------

def verify_loaded_data(
    connection,
    expected_rows,
):
    """
    Verify row counts and basic database integrity after loading.
    """

    with connection.cursor() as cursor:

        cursor.execute(
            f"""
            SELECT
                COUNT(*),
                COUNT(DISTINCT city),
                MIN(timestamp),
                MAX(timestamp)
            FROM {TABLE_NAME};
            """
        )

        (
            total_rows,
            city_count,
            min_timestamp,
            max_timestamp,
        ) = cursor.fetchone()

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT
                    city,
                    timestamp,
                    COUNT(*) AS record_count
                FROM {TABLE_NAME}
                GROUP BY
                    city,
                    timestamp
                HAVING COUNT(*) > 1
            ) duplicates;
            """
        )

        duplicate_keys = cursor.fetchone()[0]

    print("\n" + "=" * 65)
    print("POSTGRESQL LOAD VERIFICATION")
    print("=" * 65)

    print(
        f"Expected dataset rows: "
        f"{expected_rows:,}"
    )

    print(
        f"Database rows: "
        f"{total_rows:,}"
    )

    print(
        f"Cities: "
        f"{city_count}"
    )

    print(
        f"Start timestamp: "
        f"{min_timestamp}"
    )

    print(
        f"End timestamp: "
        f"{max_timestamp}"
    )

    print(
        f"Duplicate city/timestamp keys: "
        f"{duplicate_keys:,}"
    )

    if (
        total_rows == expected_rows
        and city_count == 8
        and duplicate_keys == 0
    ):
        print(
            "\nLOAD VERIFICATION: PASS"
        )

        return True

    print(
        "\nLOAD VERIFICATION: FAIL"
    )

    return False


# ---------------------------------------------------------------------
# Main load pipeline
# ---------------------------------------------------------------------

def load_to_postgres():
    """
    Run the complete PostgreSQL loading process.
    """

    print("=" * 65)
    print("POSTGRESQL DATA LOAD")
    print("=" * 65)

    print("\nLoading processed dataset...")

    dataframe = load_processed_dataset()

    print(
        f"Dataset rows: "
        f"{len(dataframe):,}"
    )

    print(
        f"Dataset columns: "
        f"{len(dataframe.columns)}"
    )

    connection = None

    try:
        print(
            "\nConnecting to PostgreSQL..."
        )

        connection = connect_to_database()

        print(
            "Database connection successful."
        )

        verify_table_exists(
            connection
        )

        print(
            f"Destination table '{TABLE_NAME}' found."
        )

        print(
            "\nLoading records into PostgreSQL..."
        )

        inserted_count = insert_dataset(
            connection,
            dataframe,
        )

        print(
            f"New rows inserted: "
            f"{inserted_count:,}"
        )

        verification_passed = verify_loaded_data(
            connection,
            len(dataframe),
        )

        if not verification_passed:
            raise RuntimeError(
                "Post-load verification failed."
            )

        print(
            "\nPostgreSQL load completed successfully."
        )

    except Exception:
        if connection is not None:
            connection.rollback()

        raise

    finally:
        if connection is not None:
            connection.close()

            print(
                "Database connection closed."
            )


if __name__ == "__main__":
    load_to_postgres()