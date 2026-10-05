-- =============================================================
-- Weather & Air Quality Analytics Pipeline
-- PostgreSQL Database Schema
-- =============================================================

-- Remove the table if it already exists.
-- Useful while developing and rebuilding the database.
DROP TABLE IF EXISTS weather_air_quality;


-- =============================================================
-- MAIN ANALYTICS TABLE
-- =============================================================

CREATE TABLE weather_air_quality (

    -- Surrogate database identifier
    id BIGSERIAL PRIMARY KEY,

    -- Location and time
    city VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- ---------------------------------------------------------
    -- Weather measurements
    -- ---------------------------------------------------------

    temperature_2m DOUBLE PRECISION,

    relative_humidity_2m DOUBLE PRECISION
        CHECK (
            relative_humidity_2m >= 0
            AND relative_humidity_2m <= 100
        ),

    precipitation DOUBLE PRECISION
        CHECK (precipitation >= 0),

    wind_speed_10m DOUBLE PRECISION
        CHECK (wind_speed_10m >= 0),

    surface_pressure DOUBLE PRECISION,

    cloud_cover DOUBLE PRECISION
        CHECK (
            cloud_cover >= 0
            AND cloud_cover <= 100
        ),

    weather_code INTEGER,

    -- ---------------------------------------------------------
    -- Air-quality measurements
    -- ---------------------------------------------------------

    pm2_5 DOUBLE PRECISION
        CHECK (pm2_5 >= 0),

    pm10 DOUBLE PRECISION
        CHECK (pm10 >= 0),

    carbon_monoxide DOUBLE PRECISION
        CHECK (carbon_monoxide >= 0),

    nitrogen_dioxide DOUBLE PRECISION
        CHECK (nitrogen_dioxide >= 0),

    sulphur_dioxide DOUBLE PRECISION
        CHECK (sulphur_dioxide >= 0),

    ozone DOUBLE PRECISION
        CHECK (ozone >= 0),

    us_aqi DOUBLE PRECISION
        CHECK (us_aqi >= 0),

    -- ---------------------------------------------------------
    -- Time features generated during transformation
    -- ---------------------------------------------------------

    date DATE NOT NULL,

    year INTEGER NOT NULL,

    month INTEGER NOT NULL
        CHECK (month BETWEEN 1 AND 12),

    day INTEGER NOT NULL
        CHECK (day BETWEEN 1 AND 31),

    hour INTEGER NOT NULL
        CHECK (hour BETWEEN 0 AND 23),

    day_of_week VARCHAR(20) NOT NULL,

    -- Prevent duplicate hourly observations for the same city
    CONSTRAINT uq_city_timestamp
        UNIQUE (city, timestamp)
);


-- =============================================================
-- INDEXES
-- =============================================================

-- Useful for filtering/grouping by city
CREATE INDEX idx_weather_air_quality_city
ON weather_air_quality (city);


-- Useful for time-series analysis
CREATE INDEX idx_weather_air_quality_timestamp
ON weather_air_quality (timestamp);


-- Useful for city-specific time-series queries
CREATE INDEX idx_weather_air_quality_city_timestamp
ON weather_air_quality (city, timestamp);


-- Useful for AQI analysis and filtering
CREATE INDEX idx_weather_air_quality_aqi
ON weather_air_quality (us_aqi);


-- Useful for date-based Tableau/SQL analysis
CREATE INDEX idx_weather_air_quality_date
ON weather_air_quality (date);