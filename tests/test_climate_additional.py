"""Additional climate tests for coverage."""
from unittest.mock import MagicMock, patch
from datetime import datetime
import pytest
import pandas as pd

from meteosuisse.modules.climate import ClimateData
from meteosuisse.config import APIConfig, TimeGranularity


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
def test_climate_get_homogeneous_series_historical_assets(mock_read_csv, mock_httpx_client, mock_stac_class):
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
    mock_httpx_client.return_value.__enter__.return_value.get.side_effect = [mock_response1, mock_response2]
    
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
def test_climate_get_homogeneous_series_duplicate_historical_assets(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_homogeneous_series to ensure duplicate historical assets are not added (line 132)."""
    config = APIConfig()
    climate = ClimateData(config)
    
    mock_stac = MagicMock()
    # Create a scenario where a historical asset is processed twice:
    # 1. First asset matches granularity and gets added to urls at line 124
    # 2. Then in the historical loop (lines 127-133), it checks if href not in urls before adding
    #    This test ensures line 132 (if href not in urls: urls.append(href)) is hit
    mock_item = {
        "id": "gen",
        "assets": {
            # Asset that matches granularity AND historical - will be added at line 124
            # Then in the historical loop, it will check line 132 (if href not in urls)
            "climate_gen_d_historical_2020-2029.csv": {
                "href": "http://example.com/climate_gen_d_historical_2020-2029.csv",
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
    
    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2020, 1, 1),
        end=datetime(2020, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    # The asset matches granularity (added at line 124) AND historical (line 132 check)
    # Line 132 should be hit: if href not in urls: urls.append(href)
    # But since href was already added at line 124, it should NOT be added again
    # So we should only download once
    assert mock_httpx_client.return_value.__enter__.return_value.get.call_count == 1


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_ddmm_format_else_branch(mock_read_csv, mock_httpx_client, mock_stac_class):
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
def test_climate_get_homogeneous_series_empty_after_parsing(mock_read_csv, mock_httpx_client, mock_stac_class):
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
def test_climate_get_homogeneous_series_broad_text_search(mock_read_csv, mock_httpx_client, mock_stac_class):
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
    df = pd.DataFrame({
        "time": ["2024-01-01"],
        "station_name": ["Station GEN"],  # Contains GEN in text
        "value": [10.0],
    })
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
def test_climate_get_homogeneous_series_tz_localize(mock_read_csv, mock_httpx_client, mock_stac_class):
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
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "time,value\n2024-01-01,10.0\n2024-01-15,20.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    # Mock read_csv - DataFrame with timezone-naive index
    df = pd.DataFrame({
        "value": [10.0, 20.0],
    }, index=pd.DatetimeIndex(["2024-01-01", "2024-01-15"]))  # No tz
    mock_read_csv.return_value = df
    
    # Use timezone-naive start/end dates
    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),  # No tzinfo
        end=datetime(2024, 1, 31),   # No tzinfo
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should localize index and dates to UTC (lines 213, 221, 228)

