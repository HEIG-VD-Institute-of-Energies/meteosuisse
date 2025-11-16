from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from meteosuisse.config import APIConfig, TimeGranularity, UpdateFrequency
from meteosuisse.modules.ground_based import GroundBasedMeasurements


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
def test_ground_based_get_automatic_weather_stations_exception_handling(mock_stac_class):
    """Test get_automatic_weather_stations exception handling (line 86)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)

    # Mock STACClient to raise exception
    mock_stac = MagicMock()
    mock_stac.search_items.side_effect = Exception("STAC error")
    mock_stac_class.return_value = mock_stac

    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
def test_ground_based_get_automatic_weather_stations_no_items(mock_stac_class):
    """Test get_automatic_weather_stations with no STAC items (line 92)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)

    mock_stac = MagicMock()
    mock_stac.search_items.return_value = []
    mock_stac_class.return_value = mock_stac

    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
def test_ground_based_get_automatic_weather_stations_no_asset_urls(mock_stac_class):
    """Test get_automatic_weather_stations with no asset URLs (line 163)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {},  # No assets
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_empty_dataframe(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_automatic_weather_stations with empty DataFrame from CSV (lines 178, 199)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            }
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv to return empty DataFrame
    mock_read_csv.return_value = pd.DataFrame()

    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
def test_ground_based_get_automatic_weather_stations_no_frames(mock_httpx_client, mock_stac_class):
    """Test get_automatic_weather_stations with no valid frames (line 211)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            }
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx to raise exception
    mock_httpx_client.return_value.__enter__.return_value.get.side_effect = Exception("HTTP error")

    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_timezone_handling(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_automatic_weather_stations timezone handling (lines 243, 250, 257)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            }
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "reference_timestamp,value\n01.01.2024 00:00,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv to return DataFrame with timezone-naive index
    df = pd.DataFrame({"value": [10.0]}, index=pd.DatetimeIndex(["2024-01-01"]))
    mock_read_csv.return_value = df

    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),  # timezone-naive
        end=datetime(2024, 1, 31),  # timezone-naive
    )

    assert isinstance(result, pd.DataFrame)


@pytest.mark.unit
@patch("meteosuisse.modules.ground_based.STACClient")
@patch("meteosuisse.modules.ground_based.httpx.Client")
@patch("meteosuisse.modules.ground_based.pd.read_csv")
def test_ground_based_get_automatic_weather_stations_no_time_col(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_automatic_weather_stations when no time column found (line 204)."""
    config = APIConfig()
    ground = GroundBasedMeasurements(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gve",
        "assets": {
            "ogd-smn_gve_h_recent.csv": {
                "href": "http://example.com/ogd-smn_gve_h_recent.csv",
                "type": "text/csv",
            }
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "value1,value2\n10.0,20.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv to return DataFrame without time columns
    df = pd.DataFrame({"value1": [10.0], "value2": [20.0]})
    mock_read_csv.return_value = df

    result = ground.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
