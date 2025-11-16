from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import httpx
import pandas as pd

from .config import APIConfig
from .csv_parser import parse_measurement_data_csv


def download_csv_file(url: str, dest: Path, client: httpx.Client) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = client.get(url)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def merge_csv_files(paths: Iterable[Path], *, timestamp_col: str) -> pd.DataFrame:
    frames = [
        parse_measurement_data_csv(p, timestamp_col=timestamp_col) for p in paths if p.exists()
    ]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df


def fetch_data_range(
    *,
    config: APIConfig,
    urls: list[str],
    cache_paths: list[Path],
    timestamp_col: str,
    start: datetime | None,
    end: datetime | None,
) -> pd.DataFrame:
    client = httpx.Client(timeout=config.httpx_timeout(), limits=config.httpx_limits(), http2=False)
    try:
        for url, path in zip(urls, cache_paths):
            if not path.exists():
                download_csv_file(url, path, client)
        df = merge_csv_files(cache_paths, timestamp_col=timestamp_col)
        if df.empty:
            return df
        if start is not None:
            index_tz = getattr(df.index, "tz", None)
            if index_tz is not None:
                start_ts = pd.Timestamp(start, tz="UTC").tz_convert(index_tz)
            else:
                start_ts = pd.Timestamp(start)
            df = df[df.index >= start_ts]
        if end is not None:
            index_tz = getattr(df.index, "tz", None)
            if index_tz is not None:
                end_ts = pd.Timestamp(end, tz="UTC").tz_convert(index_tz)
            else:
                end_ts = pd.Timestamp(end)
            df = df[df.index <= end_ts]
        return df
    finally:
        client.close()
