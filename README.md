# Weather & Air Quality Analytics Pipeline

An end-to-end analytics engineering project that extracts historical weather
and air-quality data from Open-Meteo, transforms and validates 70,080 hourly
observations, loads them into PostgreSQL, analyzes environmental patterns with
SQL, and exports reporting datasets for Tableau Public.

![Pipeline Architecture](docs/images/pipeline_architecture.png)

## Project Highlights

| Metric | Result |
| --- | ---: |
| Hourly observations | **70,080** |
| U.S. cities | **8** |
| Days of coverage | **365** |
| Final analytical fields | **22** |
| Duplicate city/timestamp keys | **0** |
| Missing values after transformation | **0** |

## Business & Analytical Purpose

The pipeline supports comparisons of air quality across major U.S. cities and
over time. The analysis examines:

- How AQI and PM2.5 vary by city and month
- Which cities and city/month combinations have the highest average AQI
- How AQI patterns differ by hour of day and day of week
- How often cities record AQI above 100
- The relationship between wind speed, precipitation, temperature, and air-quality measures
- How PM2.5 and other pollutants differ geographically

These queries describe observed patterns and associations; they do not
establish causation.

## 2025 Dataset at a Glance

![2025 Dataset at a Glance](docs/images/data_quality_summary.png)

The historical dataset covers **2025-01-01 00:00 through 2025-12-31 23:00**
at hourly granularity. It contains 8 cities × 8,760 hours = **70,080
observations**, with `city` + `timestamp` as the observation key.

Cities:

- Salt Lake City
- Denver
- Los Angeles
- Seattle
- Chicago
- New York
- Houston
- Phoenix

## Tableau Dashboard

**Dashboard visualization layer in progress.**

The repository includes a reproducible PostgreSQL-to-CSV export layer for
Tableau Public. Planned dashboard views include:

- Average AQI by city
- Monthly average AQI by city
- AQI category distribution
- Wind speed vs. average AQI
- Average AQI by hour of day
- Average PM2.5 by city
- Average AQI, maximum AQI, average PM2.5, and hours with AQI > 100 KPIs

<!-- Add final Tableau dashboard screenshot here after dashboard completion. -->

## Tech Stack

| Technology | Purpose |
| --- | --- |
| Python | Pipeline orchestration and data processing |
| Pandas | Tabular transformation and CSV handling |
| Requests | Open-Meteo API requests |
| PostgreSQL | Analytics storage and query layer |
| SQL | Analysis and reusable analytics views |
| psycopg2-binary | PostgreSQL connectivity and bulk inserts |
| python-dotenv | Environment-based database configuration |
| Tableau Public | Planned dashboard visualization layer |
| Git / GitHub | Version control and project hosting |

## How the Pipeline Works

1. **Extract** — `src/extract/extract_historical.py` retrieves hourly weather
   observations from the Open-Meteo Archive API, while
   `src/extract/extract_historical_air_quality.py` retrieves hourly air-quality
   observations from the Open-Meteo Air Quality API. Each city response is
   saved as raw JSON under `data/raw/`.
2. **Transform** — `src/transform/transform_historical.py` converts hourly
   JSON arrays into DataFrames, merges weather and air quality by city and
   timestamp, removes invalid timestamps and exact duplicate rows, adds
   date/time features, and writes `data/processed/weather_air_quality_2025.csv`.
3. **Validate** — `src/validation/validate_data.py` checks the required
   schema, configured cities, unique city/timestamp keys, valid timestamps,
   complete 2025 endpoints, humidity and cloud-cover ranges, and
   non-negative measurements. It also reports missing values and rows by city.
4. **Load** — `src/load/load_postgres.py` inserts the processed data into
   `weather_air_quality` with an idempotent `ON CONFLICT (city, timestamp)`
   rule, then verifies row counts, city count, timestamp bounds, and duplicate
   keys.
5. **Analyze** — `sql/analysis/weather_air_quality_analysis.sql` contains
   city, monthly, hourly, weekday, AQI-category, weather-group, ranking,
   month-over-month, and worst-day analyses using aggregations, `FILTER`,
   `CASE`, CTEs, `RANK()`, `ROW_NUMBER()`, and `LAG()`.
6. **Visualize** — `src/load/export_tableau.py` exports the fact table and
   analytics views to CSV files in `data/tableau/` for Tableau Public.

## Data Quality & Validation

The validation module implements these checks:

- All 22 required columns exist
- All configured cities are present and no unexpected cities appear
- `city` + `timestamp` is unique
- Timestamps parse successfully
- The dataset begins at `2025-01-01 00:00:00` and ends at
  `2025-12-31 23:00:00`
- Relative humidity and cloud cover remain between 0 and 100
- Precipitation, wind speed, PM2.5, PM10, carbon monoxide, nitrogen dioxide,
  sulphur dioxide, ozone, and U.S. AQI are non-negative
- Missing values are reported by column before loading

The transformed project output records 70,080 rows, 22 columns, zero
duplicate city/timestamp keys, and zero missing values.

## PostgreSQL Analytics Layer

`sql/schema/create_tables.sql` creates the `weather_air_quality` table with:

- A `BIGSERIAL` primary key
- 22 loaded analytical fields plus the generated database `id`
- A unique constraint on `(city, timestamp)`
- Range checks for humidity, cloud cover, non-negative measurements, and
  calendar fields
- Indexes on city, timestamp, city/timestamp, AQI, and date

The loader reads `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`
from `.env`. After loading, it checks expected row counts, city coverage,
timestamp bounds, and duplicate keys.

`sql/schema/create_analytics_views.sql` defines these reusable views:

- `vw_city_air_quality_summary`
- `vw_monthly_air_quality`
- `vw_daily_air_quality`
- `vw_hourly_patterns`
- `vw_aqi_categories`

## SQL Analysis

The analysis script compares cities, months, hours, weekdays, AQI categories,
wind-speed groups, precipitation conditions, and temperature ranges. It also
demonstrates:

- Grouped and conditional aggregation
- PostgreSQL `FILTER` and `CASE` expressions
- CTE-based ranking and monthly comparisons
- `RANK()`, `ROW_NUMBER()`, and `LAG()` window functions
- Time-series and category analysis

## Repository Structure

```text
weather-air-quality-analysis-pipeline/
├── data/
│   ├── processed/
│   ├── raw/
│   │   ├── air_quality/
│   │   └── weather/
│   └── tableau/
├── src/
│   ├── config/
│   ├── extract/
│   ├── load/
│   ├── transform/
│   └── validation/
├── sql/
│   ├── analysis/
│   └── schema/
├── dashboard/
├── notebooks/
├── tests/
├── docs/
│   └── images/
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

Generated raw, processed, Tableau CSV, log, and virtual-environment files are
ignored by Git; directory placeholders keep the expected folders visible.

## Getting Started

```powershell
git clone https://github.com/Hypersb/weather-air-quality-analysis-pipeline.git
cd weather-air-quality-analysis-pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with local PostgreSQL settings. Use placeholders such as:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=weather_air_quality_db
DB_USER=postgres
DB_PASSWORD=your_password_here
```

The Open-Meteo endpoints used by this project do not require an API key.
`.env` is ignored by Git and `.env.example` contains empty placeholders only.

## Running the Pipeline

Run the historical extraction modules first:

```powershell
python -m src.extract.extract_historical
python -m src.extract.extract_historical_air_quality
```

Transform and validate the combined dataset:

```powershell
python -m src.transform.transform_historical
python -m src.validation.validate_data
```

Create the PostgreSQL table before the load. From a PostgreSQL installation,
run the SQL file with `psql` (if `psql` is not on `PATH`, use the executable
path from the local PostgreSQL installation):

```powershell
psql -U postgres -d weather_air_quality_db -f sql/schema/create_tables.sql
python -m src.load.load_postgres
psql -U postgres -d weather_air_quality_db -f sql/schema/create_analytics_views.sql
```

Export the table and analytics views for Tableau Public:

```powershell
python -m src.load.export_tableau
```

The exporter writes CSV files to `data/tableau/`. These generated files are
ignored by Git.

## Skills Demonstrated

- REST API integration
- Python ETL and Pandas transformation
- Data cleaning and data-quality validation
- PostgreSQL schema design and loading
- Analytical SQL, CTEs, conditional aggregation, and window functions
- Reproducible reporting-dataset exports
- Environment-based configuration and Git/GitHub workflows

## Future Improvements

Potential future work, not current functionality:

- Scheduled pipeline execution
- Incremental database loading
- Expanded city coverage
- Automated tests and CI validation
- Cloud-hosted PostgreSQL
- Automated Tableau refresh workflow

## License

This project is released under the [MIT License](LICENSE).
