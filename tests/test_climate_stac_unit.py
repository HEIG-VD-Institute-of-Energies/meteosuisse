from io import StringIO
from datetime import datetime, timezone
import httpx
import respx
import pandas as pd
from meteosuisse.main_client import MeteoSwissClient
from meteosuisse.config import TimeGranularity


@respx.mock
def test_climate_homogeneous_series_downloads_and_parses():
    """Test basic CSV fetching and parsing for climate homogeneous series."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    # Mock STAC search - items represent stations (item.id = station code)
    search_json = {
        "features": [
            {
                "id": "gen",  # Station code in item ID
                "assets": {
                    "climate_gen_d.csv": {  # Asset name matches granularity
                        "href": "https://data.geo.admin.ch/climate/gen/climate_gen_d.csv",
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
    # Mock CSV
    csv = "time,station,value\n2024-01-01T00:00:00Z,GEN,1\n2024-01-02T00:00:00Z,GEN,2\n"
    respx.get("https://data.geo.admin.ch/climate/gen/climate_gen_d.csv").mock(
        return_value=httpx.Response(200, text=csv)
    )

    client = MeteoSwissClient()
    # Force collection id to be non-empty for this test
    client.climate.collections.climate_stations_homogeneous = "ch.meteoschweiz.ogd-climate-homogeneous"
    df = client.climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
    )
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.is_monotonic_increasing
    # Verify timezone-aware timestamps
    assert df.index.tz is not None


@respx.mock
def test_climate_homogeneous_series_date_filtering():
    """Test date range filtering for climate homogeneous series."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gen",
                "assets": {
                    "climate_gen_d.csv": {
                        "href": "https://data.geo.admin.ch/climate/gen/climate_gen_d.csv",
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
    csv = "time,station,value\n2024-01-01T00:00:00Z,GEN,1\n2024-01-02T00:00:00Z,GEN,2\n2024-01-03T00:00:00Z,GEN,3\n"
    respx.get("https://data.geo.admin.ch/climate/gen/climate_gen_d.csv").mock(
        return_value=httpx.Response(200, text=csv)
    )

    client = MeteoSwissClient()
    client.climate.collections.climate_stations_homogeneous = "ch.meteoschweiz.ogd-climate-homogeneous"
    start = datetime(2024, 1, 2, tzinfo=timezone.utc)
    end = datetime(2024, 1, 2, 23, 59, tzinfo=timezone.utc)
    df = client.climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
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
def test_climate_homogeneous_series_station_filtering():
    """Test station filtering for climate homogeneous series."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gen",
                "assets": {
                    "climate_gen_d.csv": {
                        "href": "https://data.geo.admin.ch/climate/gen/climate_gen_d.csv",
                        "type": "text/csv",
                    }
                },
                "links": [],
            }
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    # CSV with multiple stations
    csv = "time,station,value\n2024-01-01T00:00:00Z,GEN,1\n2024-01-01T00:00:00Z,BER,2\n"
    respx.get("https://data.geo.admin.ch/climate/gen/climate_gen_d.csv").mock(
        return_value=httpx.Response(200, text=csv)
    )

    client = MeteoSwissClient()
    client.climate.collections.climate_stations_homogeneous = "ch.meteoschweiz.ogd-climate-homogeneous"
    df = client.climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
    )
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    # Should only include GEN station data
    if "station" in df.columns:
        assert all(df["station"].str.upper() == "GEN")


@respx.mock
def test_climate_homogeneous_series_no_station_id():
    """Test getting data for all stations (no station_id filter)."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gen",
                "assets": {
                    "climate_gen_d.csv": {
                        "href": "https://data.geo.admin.ch/climate/gen/climate_gen_d.csv",
                        "type": "text/csv",
                    }
                },
                "links": [],
            },
            {
                "id": "ber",
                "assets": {
                    "climate_ber_d.csv": {
                        "href": "https://data.geo.admin.ch/climate/ber/climate_ber_d.csv",
                        "type": "text/csv",
                    }
                },
                "links": [],
            },
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    csv_gen = "time,station,value\n2024-01-01T00:00:00Z,GEN,1\n"
    respx.get("https://data.geo.admin.ch/climate/gen/climate_gen_d.csv").mock(
        return_value=httpx.Response(200, text=csv_gen)
    )

    csv_ber = "time,station,value\n2024-01-01T00:00:00Z,BER,2\n"
    respx.get("https://data.geo.admin.ch/climate/ber/climate_ber_d.csv").mock(
        return_value=httpx.Response(200, text=csv_ber)
    )

    client = MeteoSwissClient()
    client.climate.collections.climate_stations_homogeneous = "ch.meteoschweiz.ogd-climate-homogeneous"
    df = client.climate.get_homogeneous_series(
        station_id=None,
        granularity=TimeGranularity.DAILY,
    )
    assert isinstance(df, pd.DataFrame)
    # Should include data from multiple stations
    assert not df.empty


@respx.mock
def test_climate_homogeneous_series_different_granularities():
    """Test different granularities for climate data."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {
        "features": [
            {
                "id": "gen",
                "assets": {
                    "climate_gen_d.csv": {
                        "href": "https://data.geo.admin.ch/climate/gen/climate_gen_d.csv",
                        "type": "text/csv",
                    },
                    "climate_gen_m.csv": {
                        "href": "https://data.geo.admin.ch/climate/gen/climate_gen_m.csv",
                        "type": "text/csv",
                    },
                },
                "links": [],
            }
        ],
        "links": [],
    }
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    csv_d = "time,station,value\n2024-01-01T00:00:00Z,GEN,1\n"
    respx.get("https://data.geo.admin.ch/climate/gen/climate_gen_d.csv").mock(
        return_value=httpx.Response(200, text=csv_d)
    )

    client = MeteoSwissClient()
    client.climate.collections.climate_stations_homogeneous = "ch.meteoschweiz.ogd-climate-homogeneous"
    
    # Test daily
    df_d = client.climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.DAILY,
    )
    assert isinstance(df_d, pd.DataFrame)
    assert not df_d.empty
    assert isinstance(df_d.index, pd.DatetimeIndex)

    csv_m = "time,station,value\n2024-01-01T00:00:00Z,GEN,30\n"
    respx.get("https://data.geo.admin.ch/climate/gen/climate_gen_m.csv").mock(
        return_value=httpx.Response(200, text=csv_m)
    )

    # Test monthly
    df_m = client.climate.get_homogeneous_series(
        station_id="GEN",
        granularity=TimeGranularity.MONTHLY,
    )
    assert isinstance(df_m, pd.DataFrame)
    assert not df_m.empty
    assert isinstance(df_m.index, pd.DatetimeIndex)


@respx.mock
def test_climate_homogeneous_series_empty_result():
    """Test that empty DataFrame is returned when no data found."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {"features": [], "links": []}
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    client.climate.collections.climate_stations_homogeneous = "ch.meteoschweiz.ogd-climate-homogeneous"
    df = client.climate.get_homogeneous_series(
        station_id="NONEXISTENT",
        granularity=TimeGranularity.DAILY,
    )
    assert isinstance(df, pd.DataFrame)
    assert df.empty


