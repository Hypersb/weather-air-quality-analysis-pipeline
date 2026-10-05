"""
Tableau data export pipeline.

Exports analytics-ready PostgreSQL tables and views to CSV files
for visualization in Tableau Public.
"""

import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


# =============================================================
# PROJECT CONFIGURATION
# =============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

OUTPUT_DIR = PROJECT_ROOT / "data" / "tableau"


# PostgreSQL source -> Tableau CSV filename
EXPORTS = {
    "weather_air_quality": "hourly_weather_air_quality.csv",
    "vw_city_air_quality_summary": "city_air_quality_summary.csv",
    "vw_monthly_air_quality": "monthly_air_quality.csv",
    "vw_daily_air_quality": "daily_air_quality.csv",
    "vw_hourly_patterns": "hourly_patterns.csv",
    "vw_aqi_categories": "aqi_categories.csv",
}


# =============================================================
# DATABASE CONFIGURATION
# =============================================================

def load_database_config():
    """
    Load PostgreSQL connection settings from .env.
    """

    load_dotenv(ENV_FILE)

    config = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }

    missing = [
        key
        for key, value in config.items()
        if not value
    ]

    if missing:
        raise ValueError(
            "Missing database environment variables: "
            + ", ".join(missing)
        )

    return config


# =============================================================
# DATABASE CONNECTION
# =============================================================

def connect_to_database():
    """
    Connect to PostgreSQL.
    """

    config = load_database_config()

    return psycopg2.connect(**config)


# =============================================================
# EXPORT FUNCTIONS
# =============================================================

def export_query(
    connection,
    source_name,
    output_filename,
):
    """
    Export a PostgreSQL table or view to CSV.
    """

    query = f"""
        SELECT *
        FROM {source_name};
    """

    dataframe = pd.read_sql_query(
        query,
        connection,
    )

    output_path = (
        OUTPUT_DIR
        / output_filename
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    return {
        "source": source_name,
        "file": output_filename,
        "rows": len(dataframe),
        "columns": len(dataframe.columns),
        "path": output_path,
    }


# =============================================================
# EXPORT VALIDATION
# =============================================================

def validate_export(export_result):
    """
    Confirm that an exported CSV exists and contains data.
    """

    path = export_result["path"]

    if not path.exists():
        raise RuntimeError(
            f"Export file was not created: {path}"
        )

    if path.stat().st_size == 0:
        raise RuntimeError(
            f"Export file is empty: {path}"
        )

    if export_result["rows"] == 0:
        raise RuntimeError(
            f"Source returned zero rows: "
            f"{export_result['source']}"
        )


# =============================================================
# MAIN EXPORT PIPELINE
# =============================================================

def export_tableau_data():
    """
    Export all Tableau-ready datasets from PostgreSQL.
    """

    print("=" * 65)
    print("TABLEAU DATA EXPORT")
    print("=" * 65)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = None
    results = []

    try:
        print("\nConnecting to PostgreSQL...")

        connection = connect_to_database()

        print("Database connection successful.")

        print("\nExporting Tableau datasets...\n")

        for source_name, filename in EXPORTS.items():

            print(
                f"Exporting {source_name}..."
            )

            result = export_query(
                connection,
                source_name,
                filename,
            )

            validate_export(result)

            results.append(result)

            print(
                f"  Rows: {result['rows']:,}"
            )

            print(
                f"  Columns: {result['columns']}"
            )

            print(
                f"  Saved: {result['file']}\n"
            )

        print("=" * 65)
        print("TABLEAU EXPORT SUMMARY")
        print("=" * 65)

        total_rows = 0

        for result in results:

            total_rows += result["rows"]

            print(
                f"{result['file']:<40} "
                f"{result['rows']:>8,} rows"
            )

        print("-" * 65)

        print(
            f"Files exported: {len(results)}"
        )

        print(
            f"Total exported rows: {total_rows:,}"
        )

        print(
            f"Output directory:\n{OUTPUT_DIR}"
        )

        print("\nTABLEAU EXPORT: PASS")

    except Exception:
        print("\nTABLEAU EXPORT: FAIL")
        raise

    finally:
        if connection is not None:
            connection.close()

            print(
                "Database connection closed."
            )


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == "__main__":
    export_tableau_data()