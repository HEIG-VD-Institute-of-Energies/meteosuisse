from __future__ import annotations

from pathlib import Path
from typing import Iterator, Sequence

import pandas as pd


def _read_csv(
    path: Path, *, parse_dates: Sequence[str] | None = None, chunksize: int | None = None
) -> pd.DataFrame:
    if chunksize:
        chunks: Iterator[pd.DataFrame] = pd.read_csv(
            path, parse_dates=list(parse_dates or []), chunksize=chunksize
        )
        return pd.concat(chunks, ignore_index=True)
    return pd.read_csv(path, parse_dates=list(parse_dates or []))


def parse_stations_csv(path: Path) -> pd.DataFrame:
    df = _read_csv(path)
    return df


def parse_parameters_csv(path: Path) -> pd.DataFrame:
    df = _read_csv(path)
    return df


def parse_data_inventory_csv(path: Path) -> pd.DataFrame:
    df = (
        _read_csv(path, parse_dates=["start_date", "end_date"]) if path.exists() else pd.DataFrame()
    )
    return df


def parse_measurement_data_csv(path: Path, *, timestamp_col: str) -> pd.DataFrame:
    df = _read_csv(path, parse_dates=[timestamp_col])
    if timestamp_col in df.columns:
        df = df.set_index(timestamp_col).sort_index()
    return df
