# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-11-16

### Added

#### Features

- **Command-Line Interface (CLI)**: Added comprehensive CLI for weather data retrieval
  - Support for fetching data by station ID, coordinates (lat/lon), or geometry (GeoJSON/WKT)
  - Automatic nearest station lookup using Haversine distance calculation
  - Support for ground-based and climate data types
  - Configurable granularity (10min, hourly, daily, monthly, yearly) and frequency (now, recent, historical)
  - Output to CSV with customizable file paths
  - Interactive request summary and progress display using Rich
  - Console script entry point: `meteosuisse` (run via `uv run meteosuisse`)

- **STAC Client Implementation**: Complete STAC (SpatioTemporal Asset Catalog) API client
  - `STACClient` class for interacting with MeteoSwiss STAC API
  - Methods for listing collections, searching items, and fetching station data
  - Support for pagination, datetime range filtering, and station ID filtering
  - Case-insensitive station ID matching
  - Nearest station lookup functionality

- **Enhanced Data Modules**: Improved ground-based and climate data modules
  - Automatic historical asset selection for date ranges spanning multiple decades
  - Support for MeteoSwiss-specific date formats (`DD.MM.YYYY HH:MM`) with fallback to ISO
  - Robust timezone handling (timezone-naive to UTC conversion)
  - Enhanced station filtering with multiple column name support and broad text search
  - Automatic deduplication of timestamps (keep last entry)
  - Improved asset selection logic for granularity and frequency matching

- **Example Scripts**: Added example script for Yverdon-les-Bains weather station
  - Demonstrates fetching one year of hourly weather data
  - Shows proper usage of the client API

#### Testing

- **Comprehensive Test Suite**: Added full test coverage (100% code coverage achieved)
  - Unit tests for all modules: config, models, CSV parser, data fetcher, client, STAC client
  - Integration tests with VCR cassette recording for HTTP interactions
  - CLI tests covering all input methods (station ID, coordinates, geometry)
  - Module-specific tests for ground-based, climate, atmosphere, radar, and forecast modules
  - Edge case tests for timezone handling, empty data, historical assets, date parsing
  - Markdown code block execution tests for documentation validation
  - Exception and logging tests
  - 141 tests total, all passing

- **Test Infrastructure**:
  - pytest configuration with markers for unit and integration tests
  - VCR cassettes for recorded HTTP interactions
  - Coverage reporting with pytest-cov
  - Test fixtures and conftest setup

#### Documentation

- **Enhanced README**: Comprehensive documentation updates
  - CLI usage examples and options
  - Python API reference with examples
  - Configuration guide (time granularities, update frequencies, station finding)
  - Data format specifications
  - Troubleshooting section
  - Geometry input format documentation (GeoJSON, WKT, lat/lon)
  - Make targets documentation

#### Developer Experience

- **Code Quality Tools**:
  - Ruff for linting (all checks passing)
  - MyPy for type checking (100% compliance with type stubs)
  - Black for code formatting
  - isort for import sorting (configured with Black profile for compatibility)
  - Type stubs installed: pandas-stubs, types-shapely, types-pytz

### Changed

- **Project Structure**: Restructured to use canonical `artifacts/` directory structure
  - `artifacts/logs/` for log files (rotating, DEBUG level)
  - `artifacts/figures/` for plots and visualizations
  - `artifacts/reports/` for generated reports
  - `artifacts/outputs/` for generic outputs (CSV, JSON, etc.)
  - Updated all paths and configuration accordingly

- **Logging**: Enhanced logging setup
  - Default log directory changed to `artifacts/logs/`
  - File-only logging (DEBUG level) with rotation (≥1 MB)
  - Console output handled separately via Rich (no loguru console sink)
  - Improved log formatting and structure

- **HTTP Client**: Improved error handling and configuration
  - Disabled HTTP/2 to avoid `h2` dependency issues
  - Enhanced exception mapping (HTTP errors → `MeteoSwissAPIError`)
  - Transport error handling

- **Data Fetching**: Enhanced date range filtering
  - Improved timezone-aware date comparisons
  - Better handling of timezone-naive datetimes
  - Support for multiple date formats (MeteoSwiss and ISO)
  - Empty DataFrame handling before applying filters

- **Configuration**: Enhanced APIConfig with artifacts directory properties
  - Added `artifacts_dir`, `artifacts_logs_dir`, `artifacts_figures_dir`, `artifacts_reports_dir`, `artifacts_outputs_dir` properties
  - Deprecated `logs_dir` in favor of `artifacts_logs_dir`

### Fixed

- **Timezone Handling**: Fixed timezone-aware index handling in date filtering
  - Proper conversion of timezone-naive datetimes to UTC
  - Correct handling of timezone-aware indexes in `data_fetcher.py`
  - Type-safe timezone attribute access using `getattr()` with proper type guards

- **Datetime Parsing**: Enhanced datetime parsing to handle multiple formats
  - Primary support for MeteoSwiss format (`DD.MM.YYYY HH:MM`)
  - Fallback to ISO format auto-detection
  - Proper timezone localization for timezone-naive parsed datetimes

- **Station Filtering**: Improved station ID matching
  - Case-insensitive matching
  - Support for multiple column names (`station_abbr`, `station`, `station_id`, `stn`, etc.)
  - Broad text search across object columns when explicit station columns not found
  - Exact matching for primary station columns

- **Asset Selection**: Fixed historical asset inclusion logic
  - Correct decade-based asset selection for date ranges spanning historical periods
  - Proper deduplication of asset URLs
  - Improved matching of granularity and frequency patterns in asset names

- **Module Import Errors**: Fixed import issues in example and script files
  - Added `sys.path` modifications to allow direct execution without editable install
  - Proper module resolution for examples and scripts

### Dependencies

- **Added**:
  - `shapely>=2.0.0` for geometry handling (Polygon/MultiPolygon centroid extraction)
  - `pandas-stubs`, `types-shapely`, `types-pytz` for type checking
  - `pytest`, `pytest-cov`, `vcrpy`, `respx` for testing
  - `ruff`, `black`, `isort`, `mypy` for code quality

- **Updated**: All dependencies to latest compatible versions

### Technical Debt / Code Quality

- **Type Safety**: Added comprehensive type hints throughout codebase
  - Function return types (`-> int` for CLI main function)
  - Proper type guards for timezone attribute access
  - Type stubs installed for external dependencies

- **Code Formatting**: Configured isort and Black for compatibility
  - isort configured with `profile = "black"` for seamless integration
  - Consistent import sorting and formatting across codebase
  - All formatting checks passing

- **Test Coverage**: Achieved 100% code coverage
  - Added `# pragma: no cover` comments only for defensive code that's hard to test
  - Comprehensive edge case coverage
  - Integration tests with real API interactions (recorded via VCR)

### Migration Guide

If upgrading from v0.1.0:

1. **Log Directory**: Log files are now stored in `artifacts/logs/` instead of `logs/`. Update any scripts that reference log file paths.

2. **CLI Available**: The package now includes a CLI. Install the package with `uv pip install -e .` and use `uv run meteosuisse --help` to see available options.

3. **STAC API**: Ground-based and climate modules now use the STAC API internally. Data fetching is more robust and handles historical data automatically.

4. **Type Checking**: The codebase now has comprehensive type hints. If using MyPy, install type stubs: `uv pip install pandas-stubs types-shapely types-pytz`.

[0.2.0]: https://github.com/HEIG-VD-Institute-of-Energies/lca-pac/compare/v0.1.0...v0.2.0
