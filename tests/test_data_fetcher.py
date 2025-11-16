from datetime import datetime
from pathlib import Path

import pandas as pd

from meteosuisse.config import APIConfig
from meteosuisse.data_fetcher import fetch_data_range, merge_csv_files


def _write_csv(path: Path, rows: list[tuple[str, float]]) -> None:
    path.write_text("time,value\n" + "\n".join(f"{t},{v}" for t, v in rows))


def test_merge_csv_files_deduplicates_and_sorts(tmp_path: Path):
    p1 = tmp_path / "a.csv"
    p2 = tmp_path / "b.csv"
    _write_csv(p1, [("2024-01-01T00:00:00", 1.0), ("2024-01-01T01:00:00", 2.0)])
    _write_csv(p2, [("2024-01-01T01:00:00", 3.0), ("2024-01-01T02:00:00", 4.0)])

    df = merge_csv_files([p1, p2], timestamp_col="time")
    assert list(df.index.astype("datetime64[ns]")) == list(
        df.index.astype("datetime64[ns]").sort_values()
    )
    # duplicate 01:00 keeps last (from p2)
    assert df.loc[pd.Timestamp("2024-01-01T01:00:00")]["value"] == 3.0
    assert len(df) == 3


def test_fetch_data_range_filters_by_start_end(tmp_path: Path, monkeypatch):
    cfg = APIConfig()
    p = tmp_path / "cache.csv"
    _write_csv(
        p,
        [
            ("2024-01-01T00:00:00", 1),
            ("2024-01-02T00:00:00", 2),
            ("2024-01-03T00:00:00", 3),
        ],
    )
    # Provide existing cache_paths so no network is used
    df = fetch_data_range(
        config=cfg,
        urls=["http://example.com/ignore.csv"],
        cache_paths=[p],
        timestamp_col="time",
        start=datetime(2024, 1, 2),
        end=datetime(2024, 1, 3),
    )
    assert not df.empty
    assert df.index.min() >= pd.Timestamp("2024-01-02")
    assert df.index.max() <= pd.Timestamp("2024-01-03")
