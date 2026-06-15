import os
import requests
import pandas as pd
import logging
from dotenv import load_dotenv
import boto3
import json
from sqlalchemy import create_engine, text


def str_column_cleaner (df, columns):
    for column in columns:
        df[column] = df[column].astype(str).str.strip()

logging.basicConfig(level=logging.INFO, filename='Open-Meteo-Log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")



s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3_bronze_key = "bronze/open_meteo/bronze_weather_data.json"
s3_silver_key = "silver/open_meteo/silver_weather_data.csv"

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 28.5383,
    "longitude": -81.3792,
    "hourly": "temperature_2m,precipitation,wind_speed_10m",
    "temperature_unit": "fahrenheit",
    "precipitation_unit": "inch",
    "timezone": "America/New_York",
    "forecast_days": 7
}

try:

    #Generating a response from Open-Meteo
    response = requests.get(url=url, timeout=10, params=params)
    response.raise_for_status()
    logging.info("Bronze Open-Meteo pull successful")

    bronze_weather_data = response.json()
    logging.info(f"Bronze keys: {list(bronze_weather_data.keys())}")

    with open("bronze_weather_data.json", "w") as file:
        json.dump(bronze_weather_data, file)

    with open("bronze_weather_data.json", "rb") as data:
        s3_client.upload_fileobj(data, S3_BUCKET_NAME, s3_bronze_key)

    logging.info("bronze_weather_data uploaded to S3.")
    print("bronze_weather_data uploaded to S3.")

    hourly_data = bronze_weather_data["hourly"]

    bronze_weather_data_count = len(hourly_data['time'])

    #Creating Silver Data layer for S3 storage
    silver_weather_data = pd.DataFrame(hourly_data)
    silver_weather_data_count = len(silver_weather_data)

    if silver_weather_data_count != bronze_weather_data_count:
        logging.error("Bronze and Silver row counts do not match." )

        raise ValueError("Bronze and Silver row counts do not match.")

    logging.info("Bronze and Silver row counts match.")

    silver_weather_data['time'] = pd.to_datetime(silver_weather_data['time'])
    silver_weather_data.to_csv('silver_weather_data.csv', index=False)

    logging.info(f"Silver row count: {len(silver_weather_data)}")
    logging.info(f"Silver columns: {silver_weather_data.columns.tolist()}")

    with open('silver_weather_data.csv', 'rb') as data:
        s3_client.upload_fileobj(data, S3_BUCKET_NAME, s3_silver_key)
    
    logging.info("silver_weather_data uploaded to S3.")
    print("silver_weather_data uploaded to S3.")

    #Setting up RDS connection for Gold Tier Data:
    engine = create_engine(
    f"postgresql+psycopg2://{os.getenv('RDS_USER')}:{os.getenv('RDS_PASSWORD')}@{os.getenv('RDS_HOST')}:{os.getenv('RDS_PORT')}/{os.getenv('RDS_NAME')}?sslmode=require"
    )

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS weather;"))



    #Gold to DB for Analytics
    gold_weather_daily = (
    silver_weather_data
    .assign(forecast_date=silver_weather_data["time"].dt.date)
    .groupby("forecast_date")
    .agg(
        avg_temperature_f = ("temperature_2m", "mean"),
        min_temperature_f = ("temperature_2m", "min"),
        max_temperature_f = ("temperature_2m", "max"),
        total_precipitation = ("precipitation", "sum"),
        avg_wind_speed_10m = ("wind_speed_10m", "mean")
        ).reset_index()
    )

    gold_weather_daily.to_sql(
        "gold_weather_data_daily",
        con=engine,
        if_exists='replace',
        schema='weather',
        index=False
    )

    gold_RDS_count = pd.read_sql(
    "SELECT COUNT(*) FROM weather.gold_weather_data_daily",
    con=engine
    ).iloc[0, 0]

    if gold_RDS_count != len(gold_weather_daily):
        logging.error("Gold RDS row count does not match Gold DataFrame row count.")
        raise ValueError("Gold RDS row count does not match Gold DataFrame row count.")

except requests.exceptions.ReadTimeout as e:
    logging.error(f"API read timeout: {e}")
    raise

except requests.exceptions.ConnectionError as e:
    logging.error(f"Connection Error hitting API: {e}")
    raise

except requests.exceptions.HTTPError as e:
    logging.error(f"General request error: {e}")
    raise