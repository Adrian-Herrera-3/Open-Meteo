# Open-Meteo Weather Pipeline

## Project Overview

This project is a Python-based data engineering pipeline that pulls hourly weather forecast data from the Open-Meteo API, stores raw and cleaned outputs in AWS S3, transforms the data into an analytics-ready Gold table, and loads the Gold layer into AWS RDS PostgreSQL.

The pipeline follows a simple medallion-style architecture:

```text
Pull → Clean → Validate → Transform → Push
```

## Architecture

```text
Open-Meteo API
    ↓
Python requests
    ↓
Bronze Layer
Raw JSON saved locally and uploaded to AWS S3
    ↓
Silver Layer
Hourly weather DataFrame cleaned, validated, saved as CSV, and uploaded to AWS S3
    ↓
Gold Layer
Daily weather summary created with pandas aggregations
    ↓
AWS RDS PostgreSQL
Gold table loaded into weather.gold_weather_data_daily
    ↓
Validation
Gold DataFrame row count compared against RDS table row count
```

## Data Source

Source: Open-Meteo Forecast API

The pipeline pulls 7 days of hourly forecast data for Orlando, Florida using:

- Temperature
- Precipitation
- Wind speed
- Fahrenheit temperature units
- Inch precipitation units
- America/New_York timezone

## Pipeline Layers

### Bronze Layer

The Bronze layer stores the raw API response as JSON.

Output:

```text
bronze/open_meteo/bronze_weather_data.json
```

Purpose:

- Preserve the original API response
- Provide a raw backup before transformation
- Support replay/debugging if later steps fail

### Silver Layer

The Silver layer converts the hourly JSON payload into a clean tabular CSV.

Output:

```text
silver/open_meteo/silver_weather_data.csv
```

Silver includes:

- time
- temperature_2m
- precipitation
- wind_speed_10m

Validation:

- Bronze hourly row count is compared against Silver DataFrame row count

### Gold Layer

The Gold layer creates a daily analytics-ready summary from the Silver hourly data.

Target table:

```text
weather.gold_weather_data_daily
```

Gold metrics include:

- forecast_date
- avg_temperature_f
- min_temperature_f
- max_temperature_f
- total_precipitation
- avg_wind_speed_10m

Validation:

- Gold DataFrame row count is compared against the RDS PostgreSQL table count

## Technologies Used

- Python
- requests
- pandas
- boto3
- python-dotenv
- SQLAlchemy
- psycopg2
- AWS S3
- AWS RDS PostgreSQL
- Logging

## Environment Variables

This project uses a `.env` file for secrets and configuration.

Example structure:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
S3_BUCKET_NAME=your_bucket_name

RDS_HOST=your_rds_endpoint
RDS_PORT=5432
RDS_NAME=your_database_name
RDS_USER=your_username
RDS_PASSWORD=your_password
```

Do not commit `.env` to GitHub.

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the pipeline:

```bash
python Open-Meteo.py
```

Expected outputs:

- Bronze JSON uploaded to S3
- Silver CSV uploaded to S3
- Gold daily table written to AWS RDS PostgreSQL
- Row count validation logged

## Validation Checks

This pipeline currently validates:

1. API request success using `response.raise_for_status()`
2. Bronze hourly row count equals Silver DataFrame row count
3. Gold DataFrame row count equals RDS Gold table row count

## Current Project Status

Completed:

- API extraction
- Bronze JSON storage in S3
- Silver CSV storage in S3
- RDS PostgreSQL connection
- Gold daily transformation
- Gold table load to RDS
- Row count validation
- Logging
