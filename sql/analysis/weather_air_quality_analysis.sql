-- =============================================================
-- Weather & Air Quality Analysis
-- Dataset: 2025 hourly observations across 8 U.S. cities
-- Database: PostgreSQL
-- =============================================================
--
-- Purpose:
-- Analyze geographic, seasonal, temporal, and weather-related
-- patterns in air quality across eight U.S. cities.
--
-- =============================================================


-- =============================================================
-- 1. CITY-LEVEL AIR QUALITY OVERVIEW
-- =============================================================
-- Which cities experienced the worst overall air quality in 2025?

SELECT
    city,
    ROUND(AVG(us_aqi)::numeric, 2) AS avg_aqi,
    ROUND(AVG(pm2_5)::numeric, 2) AS avg_pm2_5,
    ROUND(AVG(pm10)::numeric, 2) AS avg_pm10,
    ROUND(MAX(us_aqi)::numeric, 2) AS max_aqi,
    COUNT(*) AS hourly_observations
FROM weather_air_quality
GROUP BY city
ORDER BY avg_aqi DESC;


-- =============================================================
-- 2. MONTHLY AQI TRENDS BY CITY
-- =============================================================
-- How did air quality change throughout the year for each city?

SELECT
    city,
    month,
    ROUND(AVG(us_aqi)::numeric, 2) AS avg_aqi,
    ROUND(AVG(pm2_5)::numeric, 2) AS avg_pm2_5,
    ROUND(AVG(pm10)::numeric, 2) AS avg_pm10,
    ROUND(MAX(us_aqi)::numeric, 2) AS max_aqi,
    COUNT(*) AS hourly_observations
FROM weather_air_quality
GROUP BY
    city,
    month
ORDER BY
    city,
    month;


-- =============================================================
-- 3. WORST AIR-QUALITY MONTHS
-- =============================================================
-- Which city/month combinations had the highest average AQI?

SELECT
    city,
    month,
    ROUND(AVG(us_aqi)::numeric, 2) AS avg_aqi,
    ROUND(AVG(pm2_5)::numeric, 2) AS avg_pm2_5,
    ROUND(MAX(us_aqi)::numeric, 2) AS max_aqi
FROM weather_air_quality
GROUP BY
    city,
    month
ORDER BY avg_aqi DESC
LIMIT 20;


-- =============================================================
-- 4. WORST INDIVIDUAL POLLUTION HOURS
-- =============================================================
-- When and where were the highest AQI readings recorded?

SELECT
    city,
    timestamp,
    us_aqi,
    pm2_5,
    pm10,
    temperature_2m,
    relative_humidity_2m,
    wind_speed_10m,
    precipitation
FROM weather_air_quality
ORDER BY us_aqi DESC
LIMIT 25;


-- =============================================================
-- 5. AQI CATEGORY DISTRIBUTION BY CITY
-- =============================================================
-- How many hours did each city spend in each AQI category?
--
-- U.S. AQI categories:
-- 0-50   Good
-- 51-100 Moderate
-- 101-150 Unhealthy for Sensitive Groups
-- 151-200 Unhealthy
-- 201-300 Very Unhealthy
-- 301+    Hazardous

SELECT
    city,

    COUNT(*) FILTER (
        WHERE us_aqi <= 50
    ) AS good_hours,

    COUNT(*) FILTER (
        WHERE us_aqi BETWEEN 51 AND 100
    ) AS moderate_hours,

    COUNT(*) FILTER (
        WHERE us_aqi BETWEEN 101 AND 150
    ) AS unhealthy_sensitive_hours,

    COUNT(*) FILTER (
        WHERE us_aqi BETWEEN 151 AND 200
    ) AS unhealthy_hours,

    COUNT(*) FILTER (
        WHERE us_aqi BETWEEN 201 AND 300
    ) AS very_unhealthy_hours,

    COUNT(*) FILTER (
        WHERE us_aqi > 300
    ) AS hazardous_hours

FROM weather_air_quality
GROUP BY city
ORDER BY city;


-- =============================================================
-- 6. HOURS ABOVE AQI 100
-- =============================================================
-- Which cities experienced the most hours above AQI 100?

SELECT
    city,
    COUNT(*) AS total_hours,

    COUNT(*) FILTER (
        WHERE us_aqi > 100
    ) AS hours_above_100,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (WHERE us_aqi > 100)
            / COUNT(*)
        )::numeric,
        2
    ) AS pct_hours_above_100

FROM weather_air_quality
GROUP BY city
ORDER BY hours_above_100 DESC;


-- =============================================================
-- 7. CITY POLLUTION RANKING
-- =============================================================
-- Rank cities by their annual average AQI.

WITH city_air_quality AS (
    SELECT
        city,
        AVG(us_aqi) AS avg_aqi,
        AVG(pm2_5) AS avg_pm2_5,
        AVG(pm10) AS avg_pm10
    FROM weather_air_quality
    GROUP BY city
)

SELECT
    RANK() OVER (
        ORDER BY avg_aqi DESC
    ) AS aqi_rank,

    city,

    ROUND(
        avg_aqi::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        avg_pm2_5::numeric,
        2
    ) AS avg_pm2_5,

    ROUND(
        avg_pm10::numeric,
        2
    ) AS avg_pm10

FROM city_air_quality
ORDER BY aqi_rank;


-- =============================================================
-- 8. AVERAGE AQI BY HOUR OF DAY
-- =============================================================
-- At what time of day is air quality generally worst?

SELECT
    hour,
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
    ) AS avg_pm10

FROM weather_air_quality
GROUP BY hour
ORDER BY hour;


-- =============================================================
-- 9. HOURLY AQI PATTERN BY CITY
-- =============================================================
-- Do cities show different pollution patterns throughout the day?

SELECT
    city,
    hour,

    ROUND(
        AVG(us_aqi)::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        AVG(pm2_5)::numeric,
        2
    ) AS avg_pm2_5

FROM weather_air_quality
GROUP BY
    city,
    hour
ORDER BY
    city,
    hour;


-- =============================================================
-- 10. AIR QUALITY BY DAY OF WEEK
-- =============================================================
-- Does average air quality differ between weekdays?

SELECT
    day_of_week,

    ROUND(
        AVG(us_aqi)::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        AVG(pm2_5)::numeric,
        2
    ) AS avg_pm2_5,

    COUNT(*) AS hourly_observations

FROM weather_air_quality
GROUP BY day_of_week
ORDER BY avg_aqi DESC;


-- =============================================================
-- 11. WIND SPEED VS AIR QUALITY
-- =============================================================
-- Is higher wind speed associated with lower pollution?

SELECT
    CASE
        WHEN wind_speed_10m < 5 THEN '0-5'
        WHEN wind_speed_10m < 10 THEN '5-10'
        WHEN wind_speed_10m < 15 THEN '10-15'
        WHEN wind_speed_10m < 20 THEN '15-20'
        ELSE '20+'
    END AS wind_speed_group,

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
    ) AS avg_pm10

FROM weather_air_quality
GROUP BY
    CASE
        WHEN wind_speed_10m < 5 THEN '0-5'
        WHEN wind_speed_10m < 10 THEN '5-10'
        WHEN wind_speed_10m < 15 THEN '10-15'
        WHEN wind_speed_10m < 20 THEN '15-20'
        ELSE '20+'
    END
ORDER BY
    MIN(wind_speed_10m);


-- =============================================================
-- 12. PRECIPITATION VS AIR QUALITY
-- =============================================================
-- Compare pollution during dry and rainy hours.

SELECT
    CASE
        WHEN precipitation > 0
            THEN 'Rain / Precipitation'
        ELSE 'Dry'
    END AS weather_condition,

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
    ) AS avg_pm10

FROM weather_air_quality
GROUP BY
    CASE
        WHEN precipitation > 0
            THEN 'Rain / Precipitation'
        ELSE 'Dry'
    END
ORDER BY avg_aqi DESC;


-- =============================================================
-- 13. TEMPERATURE VS AIR QUALITY
-- =============================================================
-- Compare AQI across temperature ranges.

SELECT
    CASE
        WHEN temperature_2m < 32
            THEN 'Below 32 F'

        WHEN temperature_2m < 50
            THEN '32-49 F'

        WHEN temperature_2m < 68
            THEN '50-67 F'

        WHEN temperature_2m < 86
            THEN '68-85 F'

        ELSE '86 F and above'
    END AS temperature_range,

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
        AVG(ozone)::numeric,
        2
    ) AS avg_ozone

FROM weather_air_quality
GROUP BY
    CASE
        WHEN temperature_2m < 32
            THEN 'Below 32 F'

        WHEN temperature_2m < 50
            THEN '32-49 F'

        WHEN temperature_2m < 68
            THEN '50-67 F'

        WHEN temperature_2m < 86
            THEN '68-85 F'

        ELSE '86 F and above'
    END
ORDER BY
    MIN(temperature_2m);


-- =============================================================
-- 14. MONTH-OVER-MONTH AQI CHANGE
-- =============================================================
-- Use a window function to measure changes in monthly AQI.

WITH monthly_air_quality AS (
    SELECT
        city,
        month,
        AVG(us_aqi) AS avg_aqi
    FROM weather_air_quality
    GROUP BY
        city,
        month
),

monthly_change AS (
    SELECT
        city,
        month,
        avg_aqi,

        LAG(avg_aqi) OVER (
            PARTITION BY city
            ORDER BY month
        ) AS previous_month_aqi

    FROM monthly_air_quality
)

SELECT
    city,
    month,

    ROUND(
        avg_aqi::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        previous_month_aqi::numeric,
        2
    ) AS previous_month_aqi,

    ROUND(
        (
            avg_aqi
            - previous_month_aqi
        )::numeric,
        2
    ) AS aqi_change

FROM monthly_change
ORDER BY
    city,
    month;


-- =============================================================
-- 15. WORST AIR-QUALITY DAY FOR EACH CITY
-- =============================================================
-- Identify the single day with the highest average AQI
-- for every city.

WITH daily_air_quality AS (
    SELECT
        city,
        date,

        AVG(us_aqi) AS avg_aqi,
        AVG(pm2_5) AS avg_pm2_5,
        MAX(us_aqi) AS max_aqi

    FROM weather_air_quality
    GROUP BY
        city,
        date
),

ranked_days AS (
    SELECT
        city,
        date,
        avg_aqi,
        avg_pm2_5,
        max_aqi,

        ROW_NUMBER() OVER (
            PARTITION BY city
            ORDER BY avg_aqi DESC
        ) AS pollution_rank

    FROM daily_air_quality
)

SELECT
    city,
    date,

    ROUND(
        avg_aqi::numeric,
        2
    ) AS avg_aqi,

    ROUND(
        avg_pm2_5::numeric,
        2
    ) AS avg_pm2_5,

    ROUND(
        max_aqi::numeric,
        2
    ) AS max_aqi

FROM ranked_days
WHERE pollution_rank = 1
ORDER BY avg_aqi DESC;