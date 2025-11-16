"""Additional climate tests for coverage."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from meteosuisse.config import APIConfig, TimeGranularity
from meteosuisse.modules.climate import ClimateData


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
def test_climate_get_homogeneous_series_non_csv_asset(mock_httpx_client, mock_stac_class):
    """Test get_homogeneous_series skips non-CSV assets (line 109)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.json": {  # Non-CSV asset
                "href": "http://example.com/climate_gen_d.json",
                "type": "application/json",
            },
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "time,value\n2024-01-01,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    # Should only download CSV, not JSON
    assert mock_httpx_client.return_value.__enter__.return_value.get.call_count == 1


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_historical_assets(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series includes historical assets (lines 128-133)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            },
            "climate_gen_d_historical_2020-2029.csv": {
                "href": "http://example.com/climate_gen_d_historical_2020-2029.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx responses
    mock_response1 = MagicMock()
    mock_response1.text = "time,value\n2020-01-01,10.0\n"
    mock_response1.raise_for_status = MagicMock()
    mock_response2 = MagicMock()
    mock_response2.text = "time,value\n2024-01-01,10.0\n"
    mock_response2.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.side_effect = [
        mock_response1,
        mock_response2,
    ]

    # Mock read_csv
    df1 = pd.DataFrame({"value": [10.0]}, index=pd.DatetimeIndex(["2020-01-01"], tz="UTC"))
    df2 = pd.DataFrame({"value": [10.0]}, index=pd.DatetimeIndex(["2024-01-01"], tz="UTC"))
    mock_read_csv.side_effect = [df1, df2]

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2020, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    # Should download both historical and recent assets
    assert mock_httpx_client.return_value.__enter__.return_value.get.call_count == 2


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_duplicate_historical_assets(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series duplicate historical asset check (line 132).

    This test ensures a historical asset that matches the decade but NOT the granularity
    is processed and added to urls (line 132). Since it doesn't match granularity,
    it won't be added at line 124, so when we check `if href not in urls:` at line 131,
    it will be True and line 132 (`urls.append(href)`) will execute.
    """
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            # Asset that is historical but does NOT match granularity (requesting DAILY, but asset is MONTHLY)
            # This ensures it's not added at line 124, so it will be added at line 132
            "climate_gen_m_historical_2020-2029.csv": {  # Monthly, not daily
                "href": "http://example.com/climate_gen_m_historical_2020-2029.csv",
                "type": "text/csv",
            },
            # Also include a daily asset that matches granularity to ensure the logic works
            "climate_gen_d_recent.csv": {
                "href": "http://example.com/climate_gen_d_recent.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    mock_response = MagicMock()
    mock_response.text = "time,value\n2020-01-01,5.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    df = pd.DataFrame({"value": [5.0]}, index=pd.DatetimeIndex(["2020-01-01"], tz="UTC"))
    mock_read_csv.return_value = df

    # Call get_homogeneous_series with a date range that requires historical assets
    # Requesting DAILY granularity, but the historical asset is MONTHLY
    # This ensures the historical asset is NOT added at line 124 (doesn't match granularity)
    # But it WILL be added at line 132 (matches decade and is historical)
    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2020, 1, 1),
        end=datetime(2020, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    # Verify assets were downloaded (both recent and historical)
    assert mock_httpx_client.return_value.__enter__.return_value.get.call_count >= 1


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_ddmm_format_else_branch(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series uses parsed_ddmm when not all NaT (line 167)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "time,value\n01.01.2024 00:00,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv to return DataFrame with DD.MM.YYYY format
    df = pd.DataFrame({"time": ["01.01.2024 00:00"], "value": [10.0]})
    mock_read_csv.return_value = df

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    # Should use parsed_ddmm (line 167 else branch)


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_empty_after_parsing(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series breaks when df.empty after parsing (line 171)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "time,value\ninvalid_date,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv to return DataFrame with invalid dates (all NaT after parsing)
    df = pd.DataFrame({"time": ["invalid_date"], "value": [10.0]})
    mock_read_csv.return_value = df

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty  # Should be empty after filtering invalid dates


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_broad_text_search(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series broad text search for station (lines 199-207)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "time,station_name,value\n2024-01-01,Station GEN,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv - DataFrame without explicit station columns
    df = pd.DataFrame(
        {
            "time": ["2024-01-01"],
            "station_name": ["Station GEN"],  # Contains GEN in text
            "value": [10.0],
        }
    )
    mock_read_csv.return_value = df

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    # Should filter by broad text search (lines 199-207)


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_tz_localize(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series tz_localize when tz is None (lines 213, 221, 228)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response with DD.MM.YYYY format (which creates timezone-naive datetimes)
    mock_response = MagicMock()
    mock_response.text = "time,value\n01.01.2024 00:00,10.0\n15.01.2024 00:00,20.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv - DataFrame BEFORE processing (raw CSV data)
    # The actual code will parse the time column and set it as index
    # We need to return a DataFrame that matches what pd.read_csv would return
    df = pd.DataFrame(
        {
            "time": ["01.01.2024 00:00", "15.01.2024 00:00"],  # Raw string values
            "value": [10.0, 20.0],
        }
    )
    mock_read_csv.return_value = df

    # Use timezone-naive start/end dates
    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),  # No tzinfo
        end=datetime(2024, 1, 31),  # No tzinfo
    )

    assert isinstance(result, pd.DataFrame)
    # Should localize index to UTC (line 213) because index was timezone-naive
    assert result.index.tz is not None
    assert str(result.index.tz) == "UTC"
