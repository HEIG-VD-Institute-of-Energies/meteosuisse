"""Additional CLI tests for coverage."""
import os
import subprocess
import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from rich.console import Console

from meteosuisse.cli import find_nearest_station, resolve_station_id
from meteosuisse.stac_client import STACClient


@pytest.mark.unit
def test_cli_main_entry_point():
    """Test CLI main entry point (lines 481-482)."""
    # Test by importing and calling main() directly, or using -m module syntax
    result = subprocess.run(
        [sys.executable, "-m", "meteosuisse.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
        cwd=str(Path(__file__).parent.parent),
    )
    # Should exit with code 0 (help) or 2 (argument error), not crash
    assert result.returncode in [0, 2]


@pytest.mark.unit
def test_find_nearest_station_coords_length_3():
    """Test find_nearest_station with coordinates length 3 (line 78)."""
    mock_stac = MagicMock(spec=STACClient)
    mock_items = [
        {"id": "invalid", "geometry": {"type": "Point", "coordinates": [6.127742, 46.247519, 100.0]}},  # 3 coords
    ]
    mock_stac.search_items.return_value = mock_items
    console = Console()
    
    result = find_nearest_station(mock_stac, "collection_id", 46.247519, 6.127742, console, max_stations=10)
    assert result is None


@pytest.mark.unit
@patch("meteosuisse.cli.STACClient")
@patch("meteosuisse.cli.find_nearest_station")
def test_resolve_station_id_climate_data_type(mock_find_nearest, mock_stac_class):
    """Test resolve_station_id with climate data type (line 216)."""
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

