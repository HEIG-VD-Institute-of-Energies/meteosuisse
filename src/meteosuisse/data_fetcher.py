from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable
import pandas as pd
import httpx
from .config import APIConfig
from .csv_parser import parse_measurement_data_csv


def download_csv_file(url: str, dest: Path, client: httpx.Client) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = client.get(url)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def merge_csv_files(paths: Iterable[Path], *, timestamp_col: str) -> pd.DataFrame:
    frames = [parse_measurement_data_csv(p, timestamp_col=timestamp_col) for p in paths if p.exists()]
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
    client = httpx.Client(timeout=config.httpx_timeout(), limits=config.httpx_limits(), http2=True)
    try:
        for url, path in zip(urls, cache_paths):
            if not path.exists():
                download_csv_file(url, path, client)
        df = merge_csv_files(cache_paths, timestamp_col=timestamp_col)
        if start is not None:
            df = df[df.index >= pd.Timestamp(start, tz="UTC").tz_convert(None) if df.index.tz is not None else pd.Timestamp(start)]
        if end is not None:
            df = df[df.index <= pd.Timestamp(end, tz="UTC").tz_convert(None) if df.index.tz is not None else pd.Timestamp(end)]
        return df
    finally:
        client.close()


