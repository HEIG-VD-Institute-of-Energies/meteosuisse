from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from rich.console import Console

from meteosuisse.cli import find_nearest_station, haversine_distance, main, parse_geometry_input
from meteosuisse.stac_client import STACClient


@pytest.mark.unit
def test_haversine_distance_same_point():
    """Test Haversine distance calculation for same point."""
    dist = haversine_distance(46.247519, 6.127742, 46.247519, 6.127742)
    assert dist == 0.0


@pytest.mark.unit
def test_haversine_distance_known_distance():
    """Test Haversine distance calculation for known distance."""
    # Distance between Geneva (GVE) and Bern (BER) is approximately 127 km
    gve_lat, gve_lon = 46.247519, 6.127742
    ber_lat, ber_lon = 46.9481, 7.4474
    dist = haversine_distance(gve_lat, gve_lon, ber_lat, ber_lon)
    assert 120 < dist < 135  # Approximately 127 km


@pytest.mark.unit
def test_parse_geometry_input_lat_lon_string():
    """Test parsing lat,lon string."""
    result = parse_geometry_input("46.247519,6.127742")
    assert result == (46.247519, 6.127742)


@pytest.mark.unit
def test_parse_geometry_input_geojson_point():
    """Test parsing GeoJSON Point."""
    geojson = '{"type":"Point","coordinates":[6.127742,46.247519]}'
    result = parse_geometry_input(geojson)
    assert result == (46.247519, 6.127742)  # GeoJSON is [lon, lat]


@pytest.mark.unit
def test_parse_geometry_input_geojson_feature():
    """Test parsing GeoJSON Feature with Point geometry."""
    geojson = '{"type":"Feature","geometry":{"type":"Point","coordinates":[6.127742,46.247519]}}'
    result = parse_geometry_input(geojson)
    assert result == (46.247519, 6.127742)


@pytest.mark.unit
def test_parse_geometry_input_geojson_polygon():
    """Test parsing GeoJSON Polygon (should extract centroid)."""
    geojson = '{"type":"Polygon","coordinates":[[[6.127,46.247],[6.128,46.247],[6.128,46.248],[6.127,46.248],[6.127,46.247]]]}'
    result = parse_geometry_input(geojson)
    assert result is not None
    lat, lon = result
    assert 46.247 <= lat <= 46.248
    assert 6.127 <= lon <= 6.128


@pytest.mark.unit
def test_parse_geometry_input_wkt_point():
    """Test parsing WKT POINT."""
    wkt_str = "POINT(6.127742 46.247519)"
    result = parse_geometry_input(wkt_str)
    assert result == (46.247519, 6.127742)


@pytest.mark.unit
def test_parse_geometry_input_wkt_polygon():
    """Test parsing WKT POLYGON (should extract centroid)."""
    wkt_str = "POLYGON((6.127 46.247, 6.128 46.247, 6.128 46.248, 6.127 46.248, 6.127 46.247))"
    result = parse_geometry_input(wkt_str)
    assert result is not None
    lat, lon = result
    assert 46.247 <= lat <= 46.248
    assert 6.127 <= lon <= 6.128


@pytest.mark.unit
def test_parse_geometry_input_invalid():
    """Test parsing invalid geometry input."""
    result = parse_geometry_input("invalid input")
    assert result is None


@pytest.mark.unit
def test_parse_geometry_input_lat_lon_invalid_coords():
    """Test parsing lat,lon string with invalid coordinates (line 121-122)."""
    # Invalid latitude (> 90)
    result = parse_geometry_input("100,6.127742")
    assert result is None

    # Invalid longitude (> 180)
    result = parse_geometry_input("46.247519,200")
    assert result is None

    # Invalid format (not float)
    result = parse_geometry_input("not_a_number,6.127742")
    assert result is None


@pytest.mark.unit
def test_parse_geometry_input_file_path_feature(tmp_path: Path):
    """Test parsing GeoJSON file path with Feature (lines 168-170)."""
    geojson_file = tmp_path / "feature.geojson"
    geojson_file.write_text(
        '{"type":"Feature","geometry":{"type":"Point","coordinates":[6.127742,46.247519]}}'
    )
    result = parse_geometry_input(str(geojson_file))
    assert result == (46.247519, 6.127742)


@pytest.mark.unit
def test_parse_geometry_input_file_path_exception(tmp_path: Path):
    """Test parsing GeoJSON file path with exception handling (lines 178-181)."""
    # Non-existent file
    result = parse_geometry_input(str(tmp_path / "nonexistent.geojson"))
    assert result is None

    # Invalid JSON file
    invalid_file = tmp_path / "invalid.geojson"
    invalid_file.write_text("not json")
    result = parse_geometry_input(str(invalid_file))
    assert result is None


@pytest.mark.unit
def test_parse_geometry_input_file_path_polygon(tmp_path: Path):
    """Test parsing GeoJSON file path with Polygon (lines 178-179)."""
    geojson_file = tmp_path / "polygon.geojson"
    geojson_file.write_text(
        '{"type":"Polygon","coordinates":[[[6.0,46.0],[6.1,46.0],[6.1,46.1],[6.0,46.1],[6.0,46.0]]]}'
    )
    result = parse_geometry_input(str(geojson_file))
    assert result is not None
    lat, lon = result
    # Should return centroid
    assert 46.0 <= lat <= 46.1
    assert 6.0 <= lon <= 6.1


@pytest.mark.unit
def test_parse_geometry_input_file_path(tmp_path: Path):
    """Test parsing GeoJSON file path."""
    geojson_file = tmp_path / "point.geojson"
    geojson_file.write_text('{"type":"Point","coordinates":[6.127742,46.247519]}')
    result = parse_geometry_input(str(geojson_file))
    assert result == (46.247519, 6.127742)


@pytest.mark.unit
def test_find_nearest_station_no_items():
    """Test finding nearest station when no items found."""
    mock_stac = MagicMock(spec=STACClient)
    mock_stac.search_items.return_value = []
    console = Console()

    result = find_nearest_station(mock_stac, "collection_id", 46.247519, 6.127742, console)
    assert result is None


@pytest.mark.unit
def test_find_nearest_station_invalid_geometry():
    """Test finding nearest station with invalid geometry (lines 77-78, 91-92)."""
    mock_stac = MagicMock(spec=STACClient)
    mock_items = [
        {"id": "invalid", "geometry": None},
        {"id": "invalid2", "geometry": {"type": "LineString"}},
        {
            "id": "invalid3",
            "geometry": {"type": "Point", "coordinates": [6.127742]},
        },  # Wrong length (line 77-78)
        {
            "id": "invalid4",
            "geometry": {"type": "Point", "coordinates": []},
        },  # Empty coords (line 77-78)
        {
            "id": "invalid5",
            "geometry": {"type": "Point", "coordinates": [6.127742, 46.247519, 100.0]},
        },  # 3 coords (line 77-78)
    ]
    mock_stac.search_items.return_value = mock_items
    console = Console()

    result = find_nearest_station(
        mock_stac, "collection_id", 46.247519, 6.127742, console, max_stations=10
    )
    assert result is None  # Should return None when no valid geometries (line 91-92)


@pytest.mark.unit
def test_find_nearest_station_with_items():
    """Test finding nearest station with mock STAC items."""
    mock_stac = MagicMock(spec=STACClient)
    mock_items = [
        {
            "id": "gve",
            "geometry": {"type": "Point", "coordinates": [6.127742, 46.247519]},
        },
        {
            "id": "ber",
            "geometry": {"type": "Point", "coordinates": [7.4474, 46.9481]},
        },
    ]
    mock_stac.search_items.return_value = mock_items
    console = Console()

    # Search near GVE coordinates
    result = find_nearest_station(
        mock_stac, "collection_id", 46.247519, 6.127742, console, max_stations=10
    )
    assert result is not None
    station_id, distance = result
    assert station_id.upper() == "GVE"
    assert distance < 1.0  # Should be very close


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_with_station_id(
    mock_setup_logging, mock_stac_client_class, mock_client_class, tmp_path: Path, monkeypatch
):
    """Test CLI main function with --station-id."""
    import sys

    # Mock client and data
    mock_client = MagicMock()
    # Create a proper DataFrame with columns
    df = pd.DataFrame(
        {
            "temperature": [10.0, 11.0],
            "humidity": [80, 85],
            "pressure": [1013.25, 1014.0],
        },
        index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], tz="UTC"),
    )
    mock_client.ground_based.get_automatic_weather_stations.return_value = df
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    # Set up arguments
    test_args = [
        "meteosuisse",
        "--station-id",
        "GVE",
        "--start",
        "2024-01-01T00:00:00Z",
        "--end",
        "2024-01-02T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    result = main()

    # Verify calls
    mock_client.ground_based.get_automatic_weather_stations.assert_called_once()
    assert result == 0


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
@patch("meteosuisse.cli.find_nearest_station")
def test_main_with_location(
    mock_find_nearest,
    mock_setup_logging,
    mock_stac_client_class,
    mock_client_class,
    tmp_path: Path,
    monkeypatch,
):
    """Test CLI main function with --lat and --lon."""
    import sys

    # Mock client and data
    mock_client = MagicMock()
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.__len__ = lambda x: 10
    mock_df.head.return_value = MagicMock()
    mock_df.tail.return_value = MagicMock()
    mock_df.to_string.return_value = "sample data"
    mock_client.ground_based.get_automatic_weather_stations.return_value = mock_df
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    mock_find_nearest.return_value = ("GVE", 0.5)

    # Set up arguments
    test_args = [
        "meteosuisse",
        "--lat",
        "46.247519",
        "--lon",
        "6.127742",
        "--start",
        "2024-01-01T00:00:00Z",
        "--end",
        "2024-01-02T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Verify calls
    mock_find_nearest.assert_called_once()
    mock_client.ground_based.get_automatic_weather_stations.assert_called_once()
    mock_stac.close.assert_called_once()


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
@patch("meteosuisse.cli.parse_geometry_input")
@patch("meteosuisse.cli.find_nearest_station")
def test_main_with_geometry(
    mock_find_nearest,
    mock_parse_geometry,
    mock_setup_logging,
    mock_stac_client_class,
    mock_client_class,
    tmp_path: Path,
    monkeypatch,
):
    """Test CLI main function with --geometry."""
    import sys

    # Mock client and data
    mock_client = MagicMock()
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.__len__ = lambda x: 10
    mock_df.head.return_value = MagicMock()
    mock_df.tail.return_value = MagicMock()
    mock_df.to_string.return_value = "sample data"
    mock_client.ground_based.get_automatic_weather_stations.return_value = mock_df
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    mock_parse_geometry.return_value = (46.247519, 6.127742)
    mock_find_nearest.return_value = ("GVE", 0.5)

    # Set up arguments
    test_args = [
        "meteosuisse",
        "--geometry",
        "46.247519,6.127742",
        "--start",
        "2024-01-01T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    main()

    # Verify calls
    mock_parse_geometry.assert_called_once()
    mock_find_nearest.assert_called_once()
    mock_client.ground_based.get_automatic_weather_stations.assert_called_once()
    mock_stac.close.assert_called_once()


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_empty_dataframe(
    mock_setup_logging, mock_stac_client_class, mock_client_class, tmp_path: Path, monkeypatch
):
    """Test CLI main function with empty DataFrame."""
    import sys

    # Mock client and empty data
    mock_client = MagicMock()
    mock_df = MagicMock()
    mock_df.empty = True
    mock_client.ground_based.get_automatic_weather_stations.return_value = mock_df
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    # Set up arguments
    test_args = [
        "meteosuisse",
        "--station-id",
        "GVE",
        "--start",
        "2024-01-01T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    result = main()

    # Verify calls
    mock_client.ground_based.get_automatic_weather_stations.assert_called_once()
    assert result == 1  # Should return 1 for empty DataFrame
    # Should not write CSV if empty
    assert not (tmp_path / "test_output.csv").exists()


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_climate_data_type(
    mock_setup_logging, mock_stac_client_class, mock_client_class, tmp_path: Path, monkeypatch
):
    """Test CLI main function with --data-type climate."""
    import sys

    # Mock client and data
    mock_client = MagicMock()
    # Create a proper DataFrame with columns
    df = pd.DataFrame(
        {
            "temperature": [10.0, 11.0],
            "humidity": [80, 85],
            "pressure": [1013.25, 1014.0],
        },
        index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], tz="UTC"),
    )
    mock_client.climate.get_homogeneous_series.return_value = df
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    # Set up arguments
    test_args = [
        "meteosuisse",
        "--station-id",
        "GEN",
        "--data-type",
        "climate",
        "--start",
        "2024-01-01T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Run main
    result = main()

    # Verify calls
    mock_client.climate.get_homogeneous_series.assert_called_once()
    assert result == 0


@pytest.mark.unit
def test_resolve_station_id_direct():
    """Test resolve_station_id with direct station ID."""
    from rich.console import Console

    from meteosuisse.cli import resolve_station_id

    mock_client = MagicMock()
    console = Console()

    result = resolve_station_id(mock_client, "GVE", None, None, None, "ground", console)
    assert result == "GVE"


@pytest.mark.unit
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.find_nearest_station")
def test_resolve_station_id_with_lat_lon(mock_find_nearest, mock_stac_class):
    """Test resolve_station_id with lat/lon."""
    from rich.console import Console

    from meteosuisse.cli import resolve_station_id

    mock_client = MagicMock()
    mock_client.config = MagicMock()
    console = Console()

    mock_stac = MagicMock()
    mock_stac_class.return_value = mock_stac
    mock_find_nearest.return_value = ("GVE", 0.5)

    result = resolve_station_id(mock_client, None, 46.247519, 6.127742, None, "ground", console)
    assert result == "GVE"
    mock_stac.close.assert_called_once()


@pytest.mark.unit
@patch("meteosuisse.cli.parse_geometry_input")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.find_nearest_station")
def test_resolve_station_id_with_geometry(mock_find_nearest, mock_stac_class, mock_parse_geometry):
    """Test resolve_station_id with geometry."""
    from rich.console import Console

    from meteosuisse.cli import resolve_station_id

    mock_client = MagicMock()
    mock_client.config = MagicMock()
    console = Console()

    mock_stac = MagicMock()
    mock_stac_class.return_value = mock_stac
    mock_parse_geometry.return_value = (46.247519, 6.127742)
    mock_find_nearest.return_value = ("GVE", 0.5)

    result = resolve_station_id(
        mock_client, None, None, None, "46.247519,6.127742", "ground", console
    )
    assert result == "GVE"
    mock_stac.close.assert_called_once()


@pytest.mark.unit
def test_resolve_station_id_unknown_data_type():
    """Test resolve_station_id with unknown data type."""
    from rich.console import Console

    from meteosuisse.cli import resolve_station_id

    mock_client = MagicMock()
    console = Console()

    result = resolve_station_id(mock_client, None, None, None, None, "unknown", console)
    assert result is None


@pytest.mark.unit
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.find_nearest_station")
def test_resolve_station_id_climate_data_type(mock_find_nearest, mock_stac_class):
    """Test resolve_station_id with climate data type (line 216)."""
    from rich.console import Console

    from meteosuisse.cli import resolve_station_id

    mock_client = MagicMock()
    mock_client.config = MagicMock()
    console = Console()

    mock_stac = MagicMock()
    mock_stac_class.return_value = mock_stac
    mock_find_nearest.return_value = ("GEN", 0.5)

    result = resolve_station_id(mock_client, None, 46.247519, 6.127742, None, "climate", console)
    assert result == "GEN"
    # Verify it used the climate collection
    mock_find_nearest.assert_called_once()
    call_args = mock_find_nearest.call_args
    assert "ch.meteoschweiz.ogd-climate-homogeneous" in call_args[0]
    mock_stac.close.assert_called_once()


@pytest.mark.unit
def test_parse_date_iso_format():
    """Test parse_date with ISO format."""
    from meteosuisse.cli import parse_date

    result = parse_date("2024-01-01T00:00:00Z")
    assert result.tzinfo is not None


@pytest.mark.unit
def test_parse_date_yyyy_mm_dd():
    """Test parse_date with YYYY-MM-DD format."""
    from meteosuisse.cli import parse_date

    result = parse_date("2024-01-01")
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 1


@pytest.mark.unit
def test_parse_date_invalid():
    """Test parse_date with invalid format."""
    import argparse

    from meteosuisse.cli import parse_date

    with pytest.raises(argparse.ArgumentTypeError):
        parse_date("invalid-date")


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_lat_without_lon(
    mock_setup_logging, mock_stac_client_class, mock_client_class, monkeypatch
):
    """Test CLI main function with --lat but no --lon (line 362-363)."""
    import sys

    test_args = [
        "meteosuisse",
        "--lat",
        "46.247519",
        "--start",
        "2024-01-01T00:00:00Z",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit):
        main()


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_lon_without_lat(
    mock_setup_logging, mock_stac_client_class, mock_client_class, monkeypatch
):
    """Test CLI main function with --lon but no --lat (line 364-365)."""
    import sys

    # Provide --geometry to satisfy the mutually exclusive group, then --lon without --lat
    test_args = [
        "meteosuisse",
        "--geometry",
        "6.127742,46.247519",  # This satisfies the location requirement
        "--lon",
        "6.127742",  # But --lon without --lat should fail
        "--start",
        "2024-01-01T00:00:00Z",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()
    # Should exit with code 2 (argument error)
    assert exc_info.value.code == 2


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
@patch("meteosuisse.cli.resolve_station_id")
def test_main_unknown_data_type_else_branch(
    mock_resolve_station_id,
    mock_setup_logging,
    mock_stac_client_class,
    mock_client_class,
    tmp_path: Path,
    monkeypatch,
):
    """Test CLI main function else branch for unknown data type (line 447-448)."""
    from datetime import datetime

    mock_client = MagicMock()
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    mock_resolve_station_id.return_value = "GVE"

    # Patch argparse to return args with unknown data_type
    with patch("meteosuisse.cli.argparse.ArgumentParser") as mock_parser_class:
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.station_id = "GVE"
        mock_args.data_type = "unknown_type"  # This will trigger else branch (line 447)
        mock_args.start = datetime(2024, 1, 1)
        mock_args.end = None
        mock_args.output = tmp_path / "test_output.csv"
        mock_args.lat = None
        mock_args.lon = None
        mock_args.geometry = None
        mock_args.granularity = "h"
        mock_args.frequency = "recent"
        mock_args.verbose = False
        mock_parser.parse_args.return_value = mock_args
        mock_parser_class.return_value = mock_parser

        result = main()
        assert result == 1  # Should return 1 for unknown data type (line 448)


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
@patch("meteosuisse.cli.resolve_station_id")
def test_main_station_id_resolution_failed(
    mock_resolve_station_id,
    mock_setup_logging,
    mock_stac_client_class,
    mock_client_class,
    tmp_path: Path,
    monkeypatch,
):
    """Test CLI main function when station ID resolution fails (line 382-383)."""
    import sys

    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    mock_resolve_station_id.return_value = None

    test_args = [
        "meteosuisse",
        "--lat",
        "46.247519",
        "--lon",
        "6.127742",
        "--start",
        "2024-01-01T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    result = main()
    assert result == 1


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
@patch("meteosuisse.cli.resolve_station_id")
def test_main_unknown_data_type(
    mock_resolve_station_id,
    mock_setup_logging,
    mock_stac_client_class,
    mock_client_class,
    tmp_path: Path,
    monkeypatch,
):
    """Test CLI main function with unknown data type (line 447-448).

    Note: The else branch at line 447 is unreachable in normal usage because argparse
    validates choices. This test verifies the code path exists but is defensive.
    """
    import sys

    mock_client = MagicMock()
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    mock_resolve_station_id.return_value = "GVE"

    # Use valid data-type (argparse validates choices)
    test_args = [
        "meteosuisse",
        "--station-id",
        "GVE",
        "--data-type",
        "ground",
        "--start",
        "2024-01-01T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    # Mock client to not have ground_based/climate to trigger else branch
    del mock_client.ground_based
    del mock_client.climate

    result = main()
    # Should hit the else branch and return 1
    assert result == 1


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_default_output_path(
    mock_setup_logging, mock_stac_client_class, mock_client_class, tmp_path: Path, monkeypatch
):
    """Test CLI main function with default output path (line 460-464)."""
    import sys

    mock_client = MagicMock()
    # Create a proper DataFrame with columns
    df = pd.DataFrame(
        {
            "temperature": [10.0, 11.0],
            "humidity": [80, 85],
            "pressure": [1013.25, 1014.0],
        },
        index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"], tz="UTC"),
    )
    mock_client.ground_based.get_automatic_weather_stations.return_value = df
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    # Mock APIConfig to return a test output dir
    with patch("meteosuisse.cli.APIConfig") as mock_config_class:
        mock_config = MagicMock()
        mock_config.artifacts_outputs_dir = tmp_path
        mock_config_class.return_value = mock_config

        # Don't specify --output
        test_args = [
            "meteosuisse",
            "--station-id",
            "GVE",
            "--start",
            "2024-01-01T00:00:00Z",
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        result = main()
        assert result == 0


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_exception_with_verbose(
    mock_setup_logging, mock_stac_client_class, mock_client_class, tmp_path: Path, monkeypatch
):
    """Test CLI main function exception handling with --verbose (line 472-477)."""
    import sys

    mock_client = MagicMock()
    mock_client.ground_based.get_automatic_weather_stations.side_effect = Exception("Test error")
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    test_args = [
        "meteosuisse",
        "--station-id",
        "GVE",
        "--start",
        "2024-01-01T00:00:00Z",
        "--verbose",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    result = main()
    assert result == 1


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_exception_without_verbose(
    mock_setup_logging, mock_stac_client_class, mock_client_class, tmp_path: Path, monkeypatch
):
    """Test CLI main function exception handling without --verbose."""
    import sys

    mock_client = MagicMock()
    mock_client.ground_based.get_automatic_weather_stations.side_effect = Exception("Test error")
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    test_args = [
        "meteosuisse",
        "--station-id",
        "GVE",
        "--start",
        "2024-01-01T00:00:00Z",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    result = main()
    assert result == 1


@pytest.mark.integration
@patch("meteosuisse.cli.MeteoSwissClient")
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.setup_logging")
def test_main_with_end_date(
    mock_setup_logging, mock_stac_client_class, mock_client_class, tmp_path: Path, monkeypatch
):
    """Test CLI main function with end date handling (line 403-409)."""
    import sys

    mock_client = MagicMock()
    # Create a proper DataFrame with columns
    df = pd.DataFrame(
        {
            "temperature": [10.0, 11.0],
            "humidity": [80, 85],
            "pressure": [1013.25, 1014.0],
        },
        index=pd.DatetimeIndex(["2024-01-01", "2024-01-31"], tz="UTC"),
    )
    mock_client.ground_based.get_automatic_weather_stations.return_value = df
    mock_client.ground_based.collections.automatic_weather_stations = "test_collection"
    mock_client.config = MagicMock()
    mock_client_class.return_value = mock_client

    mock_stac = MagicMock()
    mock_stac_client_class.return_value = mock_stac

    # Test with end date
    test_args = [
        "meteosuisse",
        "--station-id",
        "GVE",
        "--start",
        "2024-01-01",
        "--end",
        "2024-01-31",
        "--output",
        str(tmp_path / "test_output.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    result = main()
    assert result == 0

    # Test without end date (should default to now)
    test_args2 = [
        "meteosuisse",
        "--station-id",
        "GVE",
        "--start",
        "2024-01-01",
        "--output",
        str(tmp_path / "test_output2.csv"),
    ]
    monkeypatch.setattr(sys, "argv", test_args2)

    result = main()
    assert result == 0


@pytest.mark.unit
@patch("meteosuisse.cli.parse_geometry_input")
def test_resolve_station_id_geometry_parse_fails(mock_parse_geometry):
    """Test resolve_station_id when geometry parsing fails."""
    from rich.console import Console

    from meteosuisse.cli import resolve_station_id

    mock_client = MagicMock()
    mock_client.config = MagicMock()
    console = Console()

    mock_parse_geometry.return_value = None

    result = resolve_station_id(
        mock_client, None, None, None, "invalid_geometry", "ground", console
    )
    # Should try lat/lon path, but since both are None, should return None
    assert result is None


@pytest.mark.unit
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.find_nearest_station")
def test_resolve_station_id_no_stations_found(mock_find_nearest, mock_stac_class):
    """Test resolve_station_id when no stations found."""
    from rich.console import Console

    from meteosuisse.cli import resolve_station_id

    mock_client = MagicMock()
    mock_client.config = MagicMock()
    console = Console()

    mock_stac = MagicMock()
    mock_stac_class.return_value = mock_stac
    mock_find_nearest.return_value = None

    result = resolve_station_id(mock_client, None, 46.247519, 6.127742, None, "ground", console)
    assert result is None
    mock_stac.close.assert_called_once()
