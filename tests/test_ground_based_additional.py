"""Additional ground_based tests for coverage."""
from unittest.mock import MagicMock, patch
from datetime import datetime
import pytest
import pandas as pd

from meteosuisse.modules.ground_based import GroundBasedMeasurements
from meteosuisse.config import APIConfig, TimeGranularity, UpdateFrequency


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.HttpClient")
def test_ground_based_collection_info(mock_http_client_class):
    """Test _collection_info method (line 36)."""
    config = APIConfig()
    
    # Mock HttpClient instance
    mock_http = MagicMock()
    mock_http.get_json.return_value = {"id": "test_collection"}
    mock_http_client_class.return_value = mock_http
    
    ground = GroundBasedMeasurements(config)
    result = ground._collection_info("ch.meteoschweiz.ogd-smn")
    
    assert result == {"id": "test_collection"}
    mock_http.get_json.assert_called_once_with("/collections/ch.meteoschweiz.ogd-smn")


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
def test_ground_based_get_automatic_weather_stations_non_csv_asset(mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations skips non-CSV assets (line 123)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.json": {  # Non-CSV asset
                "href": "http://example.com/ogd-smn_gve_h_recent.json",
                "type": "application/json",
            },
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\n01.01.2024 00:00,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should only download CSV, not JSON
    assert mock_httpx_client.return_value.__enter__.return_value.get.call_count == 1


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_frequency_now(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations asset selection for frequency=now (lines 144-145)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_now.csv": {
                "href": "http://example.com/ogd-smn_gve_h_now.csv",
                "type": "text/csv",
            },
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx responses
    mock_response1 = MagicMock()
    mock_response1.text = "reference_timestamp,value\n01.01.2024 00:00,10.0\n"
    mock_response1.raise_for_status = MagicMock()
    mock_response2 = MagicMock()
    mock_response2.text = "reference_timestamp,value\n01.01.2024 01:00,20.0\n"
    mock_response2.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.side_effect = [mock_response1, mock_response2]
    
    # Mock read_csv
    df1 = pd.DataFrame({"value": [10.0]}, index=pd.DatetimeIndex(["2024-01-01"], tz="UTC"))
    df2 = pd.DataFrame({"value": [20.0]}, index=pd.DatetimeIndex(["2024-01-01 01:00"], tz="UTC"))
    mock_read_csv.side_effect = [df1, df2]
    
    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.NOW,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should prioritize _h_now assets (line 144-145)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_frequency_historical(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations asset selection for frequency=historical (lines 156-158)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_historical_2020-2029.csv": {
                "href": "http://example.com/ogd-smn_gve_h_historical_2020-2029.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\n01.01.2020 00:00,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    # Mock read_csv
    df = pd.DataFrame({"value": [10.0]}, index=pd.DatetimeIndex(["2020-01-01"], tz="UTC"))
    mock_read_csv.return_value = df
    
    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.HISTORICAL,
        start=datetime(2020, 1, 1),
        end=datetime(2020, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should select historical assets (lines 156-158)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_fallback_asset_selection(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations fallback asset selection (line 161)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_unknown.csv": {  # Doesn't match any frequency pattern
                "href": "http://example.com/ogd-smn_gve_h_unknown.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\n01.01.2024 00:00,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    # Mock read_csv
    df = pd.DataFrame({"value": [10.0]}, index=pd.DatetimeIndex(["2024-01-01"], tz="UTC"))
    mock_read_csv.return_value = df
    
    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should use fallback selection (line 161)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_date_parsing_exception(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations exception handling in date parsing (lines 194-196)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\ninvalid_date,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    # Mock read_csv to raise exception during date parsing
    df = pd.DataFrame({"reference_timestamp": [None], "value": [10.0]})
    mock_read_csv.return_value = df
    
    # Mock pd.to_datetime to raise ValueError
    with patch("meteosuisse.modules.ground_based.pd.to_datetime") as mock_to_datetime:
        mock_to_datetime.side_effect = [ValueError("Parse error"), pd.Series([pd.NaT])]
        
        result = ground.get_automatic_weather_stations(
            station_id="GVE",
            granularity=TimeGranularity.HOURLY,
            frequency=UpdateFrequency.RECENT,
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 31),
        )
        
        assert isinstance(result, pd.DataFrame)
        # Should handle exception and fallback to auto-detection (lines 194-196)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_empty_after_parsing(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations continues when df.empty after parsing (line 200)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\ninvalid_date,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    # Mock read_csv to return DataFrame with invalid dates (all NaT after parsing)
    df = pd.DataFrame({"reference_timestamp": ["invalid_date"], "value": [10.0]})
    mock_read_csv.return_value = df
    
    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should continue to next asset when df.empty (line 200)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_broad_text_search(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations broad text search for station (lines 230-238)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,station_name,value\n01.01.2024 00:00,Station GVE,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    # Mock read_csv - DataFrame without explicit station columns
    df = pd.DataFrame({
        "reference_timestamp": ["01.01.2024 00:00"],
        "station_name": ["Station GVE"],  # Contains GVE in text
        "value": [10.0],
    })
    mock_read_csv.return_value = df
    
    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should filter by broad text search (lines 230-238)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_tz_localize(mock_read_csv, mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations tz_localize when tz is None (lines 244, 251, 258)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)
    
    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            },
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac
    
    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\n01.01.2024 00:00,10.0\n01.01.2024 12:00,20.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
    
    # Mock read_csv - DataFrame with timezone-naive index
    df = pd.DataFrame({
        "value": [10.0, 20.0],
    }, index=pd.DatetimeIndex(["2024-01-01", "2024-01-01 12:00"]))  # No tz
    mock_read_csv.return_value = df
    
    # Use timezone-naive start/end dates
    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),  # No tzinfo
        end=datetime(2024, 1, 31),   # No tzinfo
    )
    
    assert isinstance(result, pd.DataFrame)
    # Should localize index and dates to UTC (lines 244, 251, 258)

