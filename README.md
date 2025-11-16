# MeteoSwiss Open Data Python Interface

A typed, modular Python client for accessing MeteoSwiss Open Data (OGD), returning pandas DataFrames with robust date‑range handling across multiple source files.

Source: MeteoSwiss (must be cited when using the data).

## Features

- Modular API covering all sections A–E
- Returns pandas DataFrames with UTC datetime index
- Date range selection across multiple files (A→B)
- HTTPX client with retries and timeouts
- Loguru file logging (rotation ≥ 1 MB)
- orjson for fast JSON parsing

## Documentation

- Project docs: this `README`
- MeteoSwiss OGD docs: `https://opendatadocs.meteoswiss.ch`
- STAC API: `https://data.geo.admin.ch/api/stac/v1/`
- Sections:
  - A: `https://opendatadocs.meteoswiss.ch/a-data-groundbased/`
  - B: `https://opendatadocs.meteoswiss.ch/b-atmosphere-measurements/`
  - C: `https://opendatadocs.meteoswiss.ch/c-climate-data/`
  - D: `https://opendatadocs.meteoswiss.ch/d-radar-data/`
  - E: `https://opendatadocs.meteoswiss.ch/e-forecast-data/`

## Install

```bash
uv pip install -e .
```

## Quick Start

```python
from datetime import datetime
import pandas as pd
from meteosuisse import MeteoSwissClient, TimeGranularity, UpdateFrequency

client = MeteoSwissClient()

# List available STAC collections
collections = client.list_collections()

# Automatic weather stations (SwissMetNet), hourly data for a station and date range
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 31)
wx = client.ground_based.get_automatic_weather_stations(
    station_id="BER",
    granularity=TimeGranularity.HOURLY,
    frequency=UpdateFrequency.RECENT,
    start=start,
    end=end,
)
assert isinstance(wx, pd.DataFrame)
print(wx.head())
```

## Usage Examples

### A. Ground-based measurements

```python
# A1 - SwissMetNet hourly
wx = client.ground_based.get_automatic_weather_stations(
    station_id="LUG",
    granularity=TimeGranularity.HOURLY,
    frequency=UpdateFrequency.RECENT,
    start=None,   # from earliest
    end=None      # to latest
)

# A5 - Manual precipitation (daily)
man_precip = client.ground_based.get_manual_precipitation(
    station_id="BER",
    granularity=TimeGranularity.DAILY,
    start=datetime(2020, 1, 1),
    end=datetime(2020, 12, 31)
)
```

### C. Climate data

```python
# C1 - Homogeneous station series (daily)
clim = client.climate.get_homogeneous_series(
    station_id="GEN",
    granularity=TimeGranularity.DAILY,
    start=datetime(1981, 1, 1),
    end=datetime(2010, 12, 31)
)
```

### D. Radar data

```python
# D1 - Precipitation radar (metadata; raster assets available separately)
# In future iterations, raster downloads (PNG/NetCDF/GeoTIFF) will be resolved.
info = client.get_collection_info(client.radar.collections.precipitation_radar)
```

### E. Forecast data

```python
# E4 - Local point forecasts (~6000 locations)
# When available via STAC assets, returns time series as DataFrame
# Example placeholder for location-based access
# forecast = client.forecast.get_local_forecast(location_id="12345")
```

## API Surface (current)

- `meteosuisse.MeteoSwissClient`
  - `list_collections()` → list collections
  - `get_collection_info(collection_id)` → dict
  - `ground_based: GroundBasedMeasurements`
  - `atmosphere: AtmosphereMeasurements`
  - `climate: ClimateData`
  - `radar: RadarData`
  - `forecast: ForecastData`

Return types

- All tabular endpoints return `pandas.DataFrame` with a `DatetimeIndex` in UTC when time-based.

## Execution

```bash
uv run python -c "from meteosuisse import MeteoSwissClient; print(len(MeteoSwissClient().list_collections()))"
```

Run tests:

```bash
uv run python -m pytest
```

## Logging

A rotating file log is written to `artifacts/logs/meteosuisse.log` (DEBUG level, 1 MB rotation). Console output (if any) should use `rich` (no loguru console sink).

## Project Layout

- `src/meteosuisse/` — package code
- `data/` — cached/downloaded data
- `artifacts/figures/` — plots (generated)
- `artifacts/reports/` — rendered reports
- `artifacts/outputs/` — machine-generated outputs
- `artifacts/logs/` — log files (rotated)
- `tests/` — test suite

## Notes and Roadmap

- Atmosphere B1 radio soundings planned availability: Q1‑2026
- Some radar/forecast spatial assets require raster/GRIB/NetCDF handling (planned)
- Station/parameter/inventory metadata CSV parsing to be expanded

## Attribution

When using this data or outputs generated from it, cite: "Source: MeteoSwiss".
