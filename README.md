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

After installation, the CLI is available as a console script. Alternatively, use `uv run python -m meteosuisse.cli` without installation.

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

## Command-Line Interface (CLI)

The CLI allows fetching weather data directly from the command line and exporting to CSV.

### Installation

The CLI is available after installation:

```bash
uv pip install -e .
uv run meteosuisse --help
```

Or run directly without installation:

```bash
uv run python -m meteosuisse.cli --help
```

### Location Options

You must provide **one** of the following location specifications:

- **`--station-id`**: Direct station code (e.g., `GVE`, `BER`, `GEN`)
- **`--lat` / `--lon`**: Latitude and longitude (finds nearest station automatically)
- **`--geometry`**: Geometry string (supports multiple formats, see below)

### Geometry Input Formats

The `--geometry` option accepts various formats:

1. **lat,lon string**: `"46.247519,6.127742"`
2. **GeoJSON Point**: `'{"type":"Point","coordinates":[6.127742,46.247519]}'`
3. **GeoJSON Polygon/MultiPolygon**: `'{"type":"Polygon","coordinates":[[[6.127,46.247],...]]}'`
   - For polygons, the centroid is automatically extracted
4. **GeoJSON Feature**: `'{"type":"Feature","geometry":{...}}'`
5. **WKT POINT**: `"POINT(6.127742 46.247519)"`
6. **WKT POLYGON/MULTIPOLYGON**: `"POLYGON((6.127 46.247, 6.128 46.247, ...))"`
   - For polygons, the centroid is automatically extracted
7. **File path**: Path to a GeoJSON file

Polygon geometries (e.g., from QGIS/geopandas) are automatically converted to their centroid for station lookup.

### Date Options

- **`--start`**: Start date in ISO format (`2024-01-01T00:00:00Z`) or YYYY-MM-DD (`2024-01-01`)
- **`--end`**: End date in ISO format or YYYY-MM-DD (defaults to now if not specified)

### Data Type Options

- **`--data-type`**: `ground` (default) or `climate`
  - `ground`: Automatic weather stations (SwissMetNet)
  - `climate`: Homogeneous climate series
- **`--granularity`**: `t` (10min), `h` (hourly, default), `d` (daily), `m` (monthly), `y` (yearly)
- **`--frequency`**: `now`, `recent` (default), or `historical`

### Output Options

- **`--output`**: Output CSV file path (default: `artifacts/outputs/weather_data.csv`)
- **`--verbose`**: Enable verbose logging

### CLI Examples

```bash
# Fetch by station code (after installation)
uv run meteosuisse --station-id GVE --start 2024-01-01 --end 2024-12-31

# Or without installation
uv run python -m meteosuisse.cli --station-id GVE --start 2024-01-01 --end 2024-12-31

# Fetch by coordinates (finds nearest station)
uv run meteosuisse --lat 46.247519 --lon 6.127742 --start 2024-01-01 --end 2024-12-31

# Fetch climate data
uv run meteosuisse --station-id GEN --data-type climate --granularity d --start 2024-01-01

# Fetch with geometry (GeoJSON Point)
uv run meteosuisse --geometry '{"type":"Point","coordinates":[6.127742,46.247519]}' --start 2024-01-01

# Fetch with geometry (WKT Polygon - centroid is extracted)
uv run meteosuisse --geometry "POLYGON((6.127 46.247, 6.128 46.247, 6.128 46.248, 6.127 46.248, 6.127 46.247))" --start 2024-01-01

# Fetch with geometry (lat,lon string)
uv run meteosuisse --geometry "46.247519,6.127742" --start 2024-01-01 --output my_data.csv

# Fetch daily historical data
uv run meteosuisse --station-id BER --granularity d --frequency historical --start 2020-01-01 --end 2020-12-31
```

## Python API Usage Examples

### A. Ground-based measurements

```python
# A1 - SwissMetNet hourly (most recent data)
wx = client.ground_based.get_automatic_weather_stations(
    station_id="LUG",
    granularity=TimeGranularity.HOURLY,
    frequency=UpdateFrequency.RECENT,
    start=None,   # from earliest available
    end=None      # to latest available
)

# A1 - SwissMetNet hourly with date range
wx = client.ground_based.get_automatic_weather_stations(
    station_id="GVE",
    granularity=TimeGranularity.HOURLY,
    frequency=UpdateFrequency.RECENT,
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 31)
)

# A1 - SwissMetNet daily historical data
wx_daily = client.ground_based.get_automatic_weather_stations(
    station_id="BER",
    granularity=TimeGranularity.DAILY,
    frequency=UpdateFrequency.HISTORICAL,
    start=datetime(2020, 1, 1),
    end=datetime(2020, 12, 31)
)

# A5 - Manual precipitation (daily) - when implemented
# man_precip = client.ground_based.get_manual_precipitation(
#     station_id="BER",
#     granularity=TimeGranularity.DAILY,
#     start=datetime(2020, 1, 1),
#     end=datetime(2020, 12, 31)
# )
```

### B. Atmosphere measurements

```python
# B1 - Radio soundings (not yet implemented)
# soundings = client.atmosphere.get_radio_soundings(...)

# List available radio sounding items
items = client.atmosphere.list_radio_soundings_items(
    start_iso="2024-01-01T00:00:00Z",
    end_iso="2024-01-31T23:59:59Z",
    collection_id="ch.meteoschweiz.ogd-radiosonde"
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

# C1 - Homogeneous station series (monthly)
clim_monthly = client.climate.get_homogeneous_series(
    station_id="GEN",
    granularity=TimeGranularity.MONTHLY,
    start=datetime(1981, 1, 1),
    end=datetime(2010, 12, 31)
)
```

### D. Radar data

```python
# D1 - Precipitation radar (metadata)
info = client.get_collection_info(client.radar.collections.precipitation_radar)

# List available precipitation radar items
items = client.radar.list_precipitation_radar_items(
    start_iso="2024-01-01T00:00:00Z",
    end_iso="2024-01-31T23:59:59Z"
)
# Note: Raster downloads (PNG/NetCDF/GeoTIFF) are planned for future iterations
```

### E. Forecast data

```python
# E1 - ICON CH-1 EPS forecasts
items_ch1 = client.forecast.list_icon_ch1_eps_items(
    start_iso="2024-01-01T00:00:00Z",
    end_iso="2024-01-31T23:59:59Z"
)

# E2 - ICON CH-2 EPS forecasts
items_ch2 = client.forecast.list_icon_ch2_eps_items(
    start_iso="2024-01-01T00:00:00Z",
    end_iso="2024-01-31T23:59:59Z"
)

# E4 - Local point forecasts (~6000 locations)
items_local = client.forecast.list_local_forecast_items(
    start_iso="2024-01-01T00:00:00Z",
    end_iso="2024-01-31T23:59:59Z"
)
# Note: Full time series access is planned for future iterations
```

## API Reference

### Main Client

- **`meteosuisse.MeteoSwissClient`**
  - `list_collections()` → `list[dict]`: List all available STAC collections
  - `get_collection_info(collection_id: str)` → `dict`: Get metadata for a specific collection
  - `ground_based: GroundBasedMeasurements`: Access ground-based measurements
  - `atmosphere: AtmosphereMeasurements`: Access atmosphere measurements
  - `climate: ClimateData`: Access climate data
  - `radar: RadarData`: Access radar data
  - `forecast: ForecastData`: Access forecast data

### Ground-Based Measurements (`client.ground_based`)

- **`get_automatic_weather_stations(...)`** → `pd.DataFrame`
  - Parameters:
    - `station_id: Optional[str]`: Station code (e.g., "GVE", "BER"). If `None`, returns data for all stations.
    - `granularity: TimeGranularity`: Time granularity (`TEN_MINUTES`, `HOURLY`, `DAILY`, `MONTHLY`, `YEARLY`)
    - `frequency: UpdateFrequency`: Update frequency (`NOW`, `RECENT`, `HISTORICAL`)
    - `start: Optional[datetime]`: Start date (UTC). If `None`, from earliest available.
    - `end: Optional[datetime]`: End date (UTC). If `None`, to latest available.
  - Returns: DataFrame with UTC datetime index and station measurements
  - Collection: `ch.meteoschweiz.ogd-smn`

### Climate Data (`client.climate`)

- **`get_homogeneous_series(...)`** → `pd.DataFrame`
  - Parameters:
    - `station_id: Optional[str]`: Station code (e.g., "GEN"). If `None`, returns data for all stations.
    - `granularity: TimeGranularity`: Time granularity (`DAILY`, `MONTHLY`, `YEARLY`)
    - `start: Optional[datetime]`: Start date (UTC). If `None`, from earliest available.
    - `end: Optional[datetime]`: End date (UTC). If `None`, to latest available.
  - Returns: DataFrame with UTC datetime index and homogeneous climate measurements
  - Collection: `ch.meteoschweiz.ogd-climate-homogeneous`

### Atmosphere Measurements (`client.atmosphere`)

- **`list_radio_soundings_items(start_iso: str, end_iso: str, collection_id: str)`** → `list[dict]`
  - Returns: List of STAC items for radio soundings in the date range
  - Collection: `ch.meteoschweiz.ogd-radiosonde`

### Radar Data (`client.radar`)

- **`list_precipitation_radar_items(start_iso: str, end_iso: str)`** → `list[dict]`
  - Returns: List of STAC items for precipitation radar in the date range
  - Collection: `ch.meteoschweiz.ogd-radar-precipitation`
  - Note: Raster asset downloads are planned for future iterations

### Forecast Data (`client.forecast`)

- **`list_icon_ch1_eps_items(start_iso: str, end_iso: str)`** → `list[dict]`
  - Returns: List of STAC items for ICON CH-1 EPS forecasts
  - Collection: `ch.meteoschweiz.ogd-forecast-icon-ch1-eps`

- **`list_icon_ch2_eps_items(start_iso: str, end_iso: str)`** → `list[dict]`
  - Returns: List of STAC items for ICON CH-2 EPS forecasts
  - Collection: `ch.meteoschweiz.ogd-forecast-icon-ch2-eps`

- **`list_local_forecast_items(start_iso: str, end_iso: str)`** → `list[dict]`
  - Returns: List of STAC items for local point forecasts (~6000 locations)
  - Collection: `ch.meteoschweiz.ogd-forecast-local`

### Return Types

- **Tabular data**: All tabular endpoints return `pandas.DataFrame` with:
  - UTC `DatetimeIndex` when time-based
  - Station-specific columns (e.g., `station_abbr`, `tre200h0`, etc.)
  - Automatic deduplication and sorting by datetime
- **STAC items**: Item listing methods return `list[dict]` with STAC feature objects
- **Collection info**: Returns `dict` with STAC collection metadata

## Configuration

### Time Granularities

- `TimeGranularity.TEN_MINUTES` / `"t"`: 10-minute intervals
- `TimeGranularity.HOURLY` / `"h"`: Hourly data (default for ground-based)
- `TimeGranularity.DAILY` / `"d"`: Daily aggregates (default for climate)
- `TimeGranularity.MONTHLY` / `"m"`: Monthly aggregates
- `TimeGranularity.YEARLY` / `"y"`: Yearly aggregates

### Update Frequencies

- `UpdateFrequency.NOW` / `"now"`: Most recent data (near real-time)
- `UpdateFrequency.RECENT` / `"recent"`: Recent data (default, typically current year)
- `UpdateFrequency.HISTORICAL` / `"historical"`: Historical data (archived)

### Station Finding

When using coordinates or geometry input (CLI or programmatic), the client automatically:

1. Parses the input geometry (supports Points, Polygons, MultiPolygons, etc.)
2. Extracts coordinates (uses centroid for non-point geometries)
3. Searches available stations in the STAC collection
4. Calculates Haversine distance to find the nearest station
5. Uses that station for data retrieval

## Execution

### Python API

```bash
uv run python -c "from meteosuisse import MeteoSwissClient; print(len(MeteoSwissClient().list_collections()))"
```

### CLI

```bash
# Help (after installation)
uv run meteosuisse --help

# Or without installation
uv run python -m meteosuisse.cli --help

# Fetch data
uv run meteosuisse --station-id GVE --start 2024-01-01 --output test.csv
```

### Testing

```bash
# Run all tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=src/meteosuisse --cov-report=html

# Run specific test
uv run python -m pytest tests/test_ground_based.py -v
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

## Data Format

All tabular data is returned as pandas DataFrames with:

- **Index**: UTC `DatetimeIndex` (timezone-aware)
- **Columns**: Station measurements (varies by data type)
  - Ground-based: `station_abbr`, `tre200h0` (temperature), `rre150h0` (precipitation), etc.
  - Climate: `stationcode`, `tre200d0` (temperature), `rre150d0` (precipitation), etc.
- **Automatic handling**:
  - Date parsing (supports MeteoSwiss `DD.MM.YYYY HH:MM` and ISO formats)
  - Timezone normalization to UTC
  - Deduplication (keeps last occurrence of duplicate timestamps)
  - Chronological sorting

### Example DataFrame Output

```python
# Ground-based hourly data
                    station_abbr  tre200h0  tre200hn  tre200hx  ...
reference_timestamp                                              
2024-01-01 00:00:00+00:00      GVE      2.3      1.8      2.8  ...
2024-01-01 01:00:00+00:00      GVE      2.1      1.6      2.5  ...
...

# Climate daily data
              stationcode  tre200d0  rre150d0  ...
time                                           
1981-01-01          GEN       -2.5       0.0  ...
1981-01-02          GEN       -3.1       0.0  ...
...
```

## Notes and Roadmap

### Currently Implemented

- [X] Ground-based automatic weather stations (A1)
- [X] Climate homogeneous series (C1)
- [X] STAC item listing for radar and forecast data
- [X] CLI interface with station finding
- [X] Polygon/geometry support (extracts centroid)

### Planned

- [ ] Atmosphere B1 radio soundings full data access (planned availability: Q1‑2026)
- [ ] Raster asset downloads for radar data (PNG/NetCDF/GeoTIFF)
- [ ] Full time series access for forecast data
- [ ] Manual precipitation data (A5)
- [ ] Additional ground-based measurement types
- [ ] Enhanced station/parameter metadata parsing

## Troubleshooting

### No data returned

- Verify the station ID exists: Check available stations in the STAC collection
- Check date range: Ensure dates are within available data periods
- Try different granularity/frequency: Some stations may not have all granularities
- Check logs: See `artifacts/logs/meteosuisse.log` for detailed error messages

### Station not found with coordinates

- The search checks up to 200 stations by default (can be adjusted in code)
- Ensure coordinates are valid (lat: -90 to 90, lon: -180 to 180)
- Try using `--station-id` directly if you know the code

### CLI command not found

- Ensure the package is installed: `uv pip install -e .`
- Use `uv run meteosuisse` (not just `meteosuisse`) to run the CLI
- Or run directly without installation: `uv run python -m meteosuisse.cli --help`

## Attribution

When using this data or outputs generated from it, cite: "Source: MeteoSwiss".
