# Open-Meteo Pipeline Architecture Diagram

## Text Diagram

```text
+-------------------+
|  Open-Meteo API   |
+---------+---------+
          |
          v
+-------------------+
| Python requests   |
| API Pull          |
+---------+---------+
          |
          v
+-----------------------------+
| Bronze Layer                |
| Raw JSON                    |
| S3: bronze/open_meteo/      |
+-------------+---------------+
              |
              v
+-----------------------------+
| Silver Layer                |
| Hourly cleaned CSV          |
| S3: silver/open_meteo/      |
+-------------+---------------+
              |
              v
+-----------------------------+
| Gold Transformation         |
| Daily pandas aggregation    |
| avg/min/max temp            |
| precipitation sum           |
| avg wind speed              |
+-------------+---------------+
              |
              v
+-----------------------------+
| AWS RDS PostgreSQL          |
| Schema: weather             |
| Table: gold_weather_data_daily |
+-------------+---------------+
              |
              v
+-----------------------------+
| Validation                  |
| Gold DF count = RDS count   |
+-----------------------------+
```

## Mermaid Diagram

```mermaid
flowchart TD
    A[Open-Meteo API] --> B[Python requests API Pull]
    B --> C[Bronze Layer: Raw JSON]
    C --> D[AWS S3 bronze/open_meteo]
    C --> E[Silver Layer: Hourly DataFrame]
    E --> F[Validate Bronze Count = Silver Count]
    F --> G[AWS S3 silver/open_meteo CSV]
    E --> H[Gold Transformation: Daily Aggregation]
    H --> I[AWS RDS PostgreSQL]
    I --> J[Schema: weather]
    J --> K[Table: gold_weather_data_daily]
    K --> L[Validate Gold DF Count = RDS Count]
```
