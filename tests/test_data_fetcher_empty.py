from __future__ import annotations

from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import pytest
import pandas as pd

from meteosuisse.data_fetcher import merge_csv_files, fetch_data_range
from meteosuisse.config import APIConfig


@pytest.mark.unit
def test_merge_csv_files_empty(tmp_path: Path):
    """Test merge_csv_files with no existing files (line 23)."""
    non_existent_paths = [tmp_path / "nonexistent1.csv", tmp_path / "nonexistent2.csv"]
    result = merge_csv_files(non_existent_paths, timestamp_col="time")
    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.unit
@patch("meteosuisse.data_fetcher.httpx.Client")
@patch("meteosuisse.data_fetcher.download_csv_file")
def test_fetch_data_range_empty_result(mock_download, mock_client_class, tmp_path: Path, monkeypatch):
    """Test fetch_data_range with empty DataFrame (line 45)."""
    from unittest.mock import MagicMock
    
    config = APIConfig()
    
    # Mock httpx client to avoid actual HTTP calls
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock download_csv_file to do nothing (file won't exist, so download is attempted)
    mock_download.return_value = None
    
    # Mock merge_csv_files to return empty DataFrame
    def mock_merge(*args, **kwargs):
        return pd.DataFrame()
    
    monkeypatch.setattr("meteosuisse.data_fetcher.merge_csv_files", mock_merge)
    
    # Ensure cache file doesn't exist so download is attempted
    cache_path = tmp_path / "cache.csv"
    assert not cache_path.exists()
    
    result = fetch_data_range(
        config=config,
        urls=["http://example.com/data.csv"],
        cache_paths=[cache_path],
        timestamp_col="time",
        start=datetime(2024, 1, 1),
        end=datetime(2024, 1, 31),
    )
    
    assert isinstance(result, pd.DataFrame)
    assert result.empty

