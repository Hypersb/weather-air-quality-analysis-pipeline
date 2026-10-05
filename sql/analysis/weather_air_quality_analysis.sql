-- =============================================================
-- Weather & Air Quality Analysis
-- Dataset: 2025 hourly observations across 8 U.S. cities
-- =============================================================


-- =============================================================
-- 1. CITY-LEVEL AIR QUALITY OVERVIEW
-- =============================================================
-- Compare average AQI and major particulate pollutants across cities.

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