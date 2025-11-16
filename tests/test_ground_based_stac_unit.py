from io import StringIO
from datetime import datetime, timezone
import pandas as pd
import httpx
import respx
from meteosuisse.main_client import MeteoSwissClient
from meteosuisse.config import TimeGranularity, UpdateFrequency


@respx.mock
def test_ground_based_fetches_and_parses_csvs():
    """Test basic CSV fetching and parsing for ground-based automatic weather stations."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gve",  # Station code in item ID
                "assets": {
                    "ogd-smn_gve_h_recent.csv": {  # Asset name matches granularity/frequency
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv",
                        "type": "text/csv",
                    }
                },
                "links": [],
            }
        ],
        "links": [],
    }
    # Mock search with ids parameter (station filtering)
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    # Mock CSV response - MeteoSwiss format with reference_timestamp (DD.MM.YYYY HH:MM)
    csv = "reference_timestamp,station_abbr,tre200h0\n01.01.2024 00:00,GVE,1.0\n01.01.2024 01:00,GVE,2.0\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv").mock(
        return_value=httpx.Response(200, text=csv)
    )

    client = MeteoSwissClient()
    df = client.ground_based.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
    )
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "tre200h0" in df.columns
    assert "station_abbr" in df.columns
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.is_monotonic_increasing
    # Verify timezone-aware timestamps
    assert df.index.tz is not None
    # Verify station filtering
    assert all(df["station_abbr"].str.upper() == "GVE")


@respx.mock
def test_ground_based_date_filtering():
    """Test date range filtering for ground-based data."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gve",
                "assets": {
                    "ogd-smn_gve_h_recent.csv": {
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv",
                        "type": "text/csv",
                    }
                },
                "links": [],
            }
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    # CSV with data spanning multiple days
    csv = "reference_timestamp,station_abbr,tre200h0\n01.01.2024 00:00,GVE,1.0\n02.01.2024 00:00,GVE,2.0\n03.01.2024 00:00,GVE,3.0\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv").mock(
        return_value=httpx.Response(200, text=csv)
    )

    client = MeteoSwissClient()
    start = datetime(2024, 1, 2, tzinfo=timezone.utc)
    end = datetime(2024, 1, 2, 23, 59, tzinfo=timezone.utc)
    df = client.ground_based.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=start,
        end=end,
    )
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert isinstance(df.index, pd.DatetimeIndex)
    # Should only include data from Jan 2
    assert df.index.min() >= start
    assert df.index.max() <= end


@respx.mock
def test_ground_based_historical_assets():
    """Test that historical assets are included when date range requires them."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gve",
                "assets": {
                    "ogd-smn_gve_h_recent.csv": {
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv",
                        "type": "text/csv",
                    },
                    "ogd-smn_gve_h_historical_2020-2029.csv": {
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_historical_2020-2029.csv",
                        "type": "text/csv",
                    },
                },
                "links": [],
            }
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    # Recent CSV (2025 data)
    csv_recent = "reference_timestamp,station_abbr,tre200h0\n01.01.2025 00:00,GVE,5.0\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv").mock(
        return_value=httpx.Response(200, text=csv_recent)
    )

    # Historical CSV (2024 data)
    csv_historical = "reference_timestamp,station_abbr,tre200h0\n15.11.2024 18:00,GVE,4.0\n15.11.2024 19:00,GVE,4.5\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_historical_2020-2029.csv").mock(
        return_value=httpx.Response(200, text=csv_historical)
    )

    client = MeteoSwissClient()
    # Request data from 2024-11-15 to 2025-01-01 (spans historical and recent)
    start = datetime(2024, 11, 15, 18, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    df = client.ground_based.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=start,
        end=end,
    )
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert isinstance(df.index, pd.DatetimeIndex)
    # Should include data from both historical and recent assets
    assert len(df) >= 2
    # Verify date filtering
    assert df.index.min() >= start
    assert df.index.max() <= end


@respx.mock
def test_ground_based_no_station_id():
    """Test getting data for all stations (no station_id filter)."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gve",
                "assets": {
                    "ogd-smn_gve_h_recent.csv": {
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv",
                        "type": "text/csv",
                    }
                },
                "links": [],
            },
            {
                "id": "ber",
                "assets": {
                    "ogd-smn_ber_h_recent.csv": {
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ber/ogd-smn_ber_h_recent.csv",
                        "type": "text/csv",
                    }
                },
                "links": [],
            },
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    csv_gve = "reference_timestamp,station_abbr,tre200h0\n01.01.2024 00:00,GVE,1.0\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv").mock(
        return_value=httpx.Response(200, text=csv_gve)
    )

    csv_ber = "reference_timestamp,station_abbr,tre200h0\n01.01.2024 00:00,BER,2.0\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ber/ogd-smn_ber_h_recent.csv").mock(
        return_value=httpx.Response(200, text=csv_ber)
    )

    client = MeteoSwissClient()
    df = client.ground_based.get_automatic_weather_stations(
        station_id=None,
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
    )
    assert isinstance(df, pd.DataFrame)
    # Should include data from multiple stations
    assert not df.empty
    assert "station_abbr" in df.columns


@respx.mock
def test_ground_based_different_granularities():
    """Test different granularities (hourly, daily, monthly)."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gve",
                "assets": {
                    "ogd-smn_gve_h_recent.csv": {
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv",
                        "type": "text/csv",
                    },
                    "ogd-smn_gve_d_recent.csv": {
                        "href": "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_d_recent.csv",
                        "type": "text/csv",
                    },
                },
                "links": [],
            }
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    # Test hourly
    csv_h = "reference_timestamp,station_abbr,tre200h0\n01.01.2024 00:00,GVE,1.0\n01.01.2024 01:00,GVE,2.0\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_h_recent.csv").mock(
        return_value=httpx.Response(200, text=csv_h)
    )

    client = MeteoSwissClient()
    df_h = client.ground_based.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
    )
    assert isinstance(df_h, pd.DataFrame)
    assert not df_h.empty
    assert isinstance(df_h.index, pd.DatetimeIndex)

    # Test daily
    csv_d = "reference_timestamp,station_abbr,tre200d0\n01.01.2024 00:00,GVE,1.5\n"
    respx.get("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/gve/ogd-smn_gve_d_recent.csv").mock(
        return_value=httpx.Response(200, text=csv_d)
    )

    df_d = client.ground_based.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.DAILY,
        frequency=UpdateFrequency.RECENT,
    )
    assert isinstance(df_d, pd.DataFrame)
    assert not df_d.empty
    assert isinstance(df_d.index, pd.DatetimeIndex)


@respx.mock
def test_ground_based_empty_result():
    """Test that empty DataFrame is returned when no data found."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    # Empty search results
    search_json = {"features": [], "links": []}
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    df = client.ground_based.get_automatic_weather_stations(
        station_id="NONEXISTENT",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
    )
    assert isinstance(df, pd.DataFrame)
    assert df.empty


@respx.mock
def test_ground_based_no_assets():
    """Test handling when STAC item has no CSV assets."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gve",
                "assets": {},  # No assets
                "links": [],
            }
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    df = client.ground_based.get_automatic_weather_stations(
        station_id="GVE",
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
    )
    assert isinstance(df, pd.DataFrame)
    assert df.empty


