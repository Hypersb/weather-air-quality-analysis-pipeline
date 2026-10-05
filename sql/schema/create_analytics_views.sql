-- =============================================================
-- Weather & Air Quality Analytics Views
-- Database: PostgreSQL
-- Dataset: 2025 hourly observations across 8 U.S. cities
-- =============================================================
--
-- Purpose:
-- Create reusable analytics views for Tableau and downstream
-- reporting without modifying the underlying fact table.
--
-- =============================================================


-- =============================================================
-- 1. CITY AIR QUALITY SUMMARY
-- =============================================================

CREATE OR REPLACE VIEW vw_city_air_quality_summary AS

SELECT
    city,

    COUNT(*) AS hourly_observations,

    ROUND(
        AVG(us_aqi)::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        MAX(us_aqi)::numeric,
        2
    ) AS max_aqi,

    ROUND(
        AVG(pm2_5)::numeric,
        2
    ) AS avg_pm2_5,

    ROUND(
        AVG(pm10)::numeric,
        2
    ) AS avg_pm10,

    ROUND(
        AVG(ozone)::numeric,
        2
    ) AS avg_ozone,

    COUNT(*) FILTER (
        WHERE us_aqi > 100
    ) AS hours_above_aqi_100,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (WHERE us_aqi > 100)
            / COUNT(*)
        )::numeric,
        2
    ) AS pct_hours_above_aqi_100

FROM weather_air_quality
GROUP BY city;


-- =============================================================
-- 2. MONTHLY AIR QUALITY
-- =============================================================

CREATE OR REPLACE VIEW vw_monthly_air_quality AS

SELECT
    city,
    year,
    month,

    COUNT(*) AS hourly_observations,

    ROUND(
        AVG(us_aqi)::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        MAX(us_aqi)::numeric,
        2
    ) AS max_aqi,

    ROUND(
        AVG(pm2_5)::numeric,
        2
    ) AS avg_pm2_5,

    ROUND(
        AVG(pm10)::numeric,
        2
    ) AS avg_pm10,

    ROUND(
        AVG(ozone)::numeric,
        2
    ) AS avg_ozone

FROM weather_air_quality
GROUP BY
    city,
    year,
    month;


-- =============================================================
-- 3. DAILY AIR QUALITY
-- =============================================================

CREATE OR REPLACE VIEW vw_daily_air_quality AS

SELECT
    city,
    date,

    COUNT(*) AS hourly_observations,

    ROUND(
        AVG(us_aqi)::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        MAX(us_aqi)::numeric,
        2
    ) AS max_aqi,

    ROUND(
        AVG(pm2_5)::numeric,
        2
    ) AS avg_pm2_5,

    ROUND(
        AVG(pm10)::numeric,
        2
    ) AS avg_pm10,

    ROUND(
        AVG(temperature_2m)::numeric,
        2
    ) AS avg_temperature,

    ROUND(
        AVG(relative_humidity_2m)::numeric,
        2
    ) AS avg_humidity,

    ROUND(
        AVG(wind_speed_10m)::numeric,
        2
    ) AS avg_wind_speed,

    ROUND(
        SUM(precipitation)::numeric,
        2
    ) AS total_precipitation

FROM weather_air_quality
GROUP BY
    city,
    date;


-- =============================================================
-- 4. HOURLY AIR QUALITY PATTERNS
-- =============================================================

CREATE OR REPLACE VIEW vw_hourly_patterns AS

SELECT
    city,
    hour,

    COUNT(*) AS observations,

    ROUND(
        AVG(us_aqi)::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        AVG(pm2_5)::numeric,
        2
    ) AS avg_pm2_5,

    ROUND(
        AVG(pm10)::numeric,
        2
    ) AS avg_pm10,

    ROUND(
        AVG(temperature_2m)::numeric,
        2
    ) AS avg_temperature,

    ROUND(
        AVG(wind_speed_10m)::numeric,
        2
    ) AS avg_wind_speed

FROM weather_air_quality
GROUP BY
    city,
    hour;


-- =============================================================
-- 5. AQI CATEGORY DISTRIBUTION
-- =============================================================

CREATE OR REPLACE VIEW vw_aqi_categories AS

SELECT
    city,

    CASE
        WHEN us_aqi <= 50
            THEN 'Good'

        WHEN us_aqi <= 100
            THEN 'Moderate'

        WHEN us_aqi <= 150
            THEN 'Unhealthy for Sensitive Groups'

        WHEN us_aqi <= 200
            THEN 'Unhealthy'

        WHEN us_aqi <= 300
            THEN 'Very Unhealthy'

        ELSE 'Hazardous'
    END AS aqi_category,

    CASE
        WHEN us_aqi <= 50 THEN 1
        WHEN us_aqi <= 100 THEN 2
        WHEN us_aqi <= 150 THEN 3
        WHEN us_aqi <= 200 THEN 4
        WHEN us_aqi <= 300 THEN 5
        ELSE 6
    END AS category_order,

    COUNT(*) AS hours,

    ROUND(
        (
            100.0
            * COUNT(*)
            / SUM(COUNT(*)) OVER (
                PARTITION BY city
            )
        )::numeric,
        2
    ) AS pct_city_hours

FROM weather_air_quality
GROUP BY
    city,

    CASE
        WHEN us_aqi <= 50
            THEN 'Good'

        WHEN us_aqi <= 100
            THEN 'Moderate'

        WHEN us_aqi <= 150
            THEN 'Unhealthy for Sensitive Groups'

        WHEN us_aqi <= 200
            THEN 'Unhealthy'

        WHEN us_aqi <= 300
            THEN 'Very Unhealthy'

        ELSE 'Hazardous'
    END,

    CASE
        WHEN us_aqi <= 50 THEN 1
        WHEN us_aqi <= 100 THEN 2
        WHEN us_aqi <= 150 THEN 3
        WHEN us_aqi <= 200 THEN 4
        WHEN us_aqi <= 300 THEN 5
        ELSE 6
    END;