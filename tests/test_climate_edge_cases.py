from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from meteosuisse.config import APIConfig, TimeGranularity
from meteosuisse.modules.climate import ClimateData


@pytest.mark.unit
def test_climate_get_homogeneous_series_no_collection(monkeypatch):
    """Test get_homogeneous_series when collection is not set (line 52)."""
    config = APIConfig()
    climate = ClimateData(config)

    # Mock collections to have no climate_stations_homogeneous
    monkeypatch.setattr(climate.collections, "climate_stations_homogeneous", None)

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
def test_climate_get_homogeneous_series_exception_handling(mock_stac_class):
    """Test get_homogeneous_series exception handling (line 80)."""
    config = APIConfig()
    climate = ClimateData(config)

    # Mock STACClient to raise exception
    mock_stac = MagicMock()
    mock_stac.search_items.side_effect = Exception("STAC error")
    mock_stac_class.return_value = mock_stac

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
def test_climate_get_homogeneous_series_no_items(mock_httpx_client, mock_stac_class):
    """Test get_homogeneous_series with no STAC items (line 85)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_stac.search_items.return_value = []
    mock_stac_class.return_value = mock_stac

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
def test_climate_get_homogeneous_series_no_urls(mock_httpx_client, mock_stac_class):
    """Test get_homogeneous_series with no asset URLs (line 135)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {},  # No assets
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_empty_dataframe(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series with empty DataFrame from CSV (line 149)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            }
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "time,value\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv to return empty DataFrame
    mock_read_csv.return_value = pd.DataFrame()

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
def test_climate_get_homogeneous_series_no_frames(mock_httpx_client, mock_stac_class):
    """Test get_homogeneous_series with no valid frames (line 181)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            }
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx to raise exception
    mock_httpx_client.return_value.__enter__.return_value.get.side_effect = Exception("HTTP error")

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.modules.climate.STACClient")
@patch("meteosuisse.modules.climate.httpx.Client")
@patch("meteosuisse.modules.climate.pd.read_csv")
def test_climate_get_homogeneous_series_timezone_handling(
    mock_read_csv, mock_httpx_client, mock_stac_class
):
    """Test get_homogeneous_series timezone handling (lines 212, 220, 227)."""
    config = APIConfig()
    climate = ClimateData(config)

    mock_stac = MagicMock()
    mock_item = {
        "id": "gen",
        "assets": {
            "climate_gen_d.csv": {
                "href": "http://example.com/climate_gen_d.csv",
                "type": "text/csv",
            }
        },
    }
    mock_stac.search_items.return_value = [mock_item]
    mock_stac_class.return_value = mock_stac

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.text = "time,value\n2024-01-01,10.0\n"
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response

    # Mock read_csv to return DataFrame with timezone-naive index
    df = pd.DataFrame({"value": [10.0]}, index=pd.DatetimeIndex(["2024-01-01"]))
    mock_read_csv.return_value = df

    result = climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
        start=datetime(2024, 1, 1),  # timezone-naive
        end=datetime(2024, 1, 31),  # timezone-naive
    )

    assert isinstance(result, pd.DataFrame)
