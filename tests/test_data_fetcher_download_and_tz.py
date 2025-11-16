from pathlib import Path
import pandas as pd
import respx
import httpx
from meteosuisse.data_fetcher import download_csv_file, fetch_data_range
from meteosuisse.config import APIConfig


@respx.mock
def test_download_csv_file_writes(tmp_path: Path):
    url = "https://example.com/data.csv"
    csv = "time,value\n2024-01-01T00:00:00Z,1\n"
    respx.get(url).mock(return_value=httpx.Response(200, text=csv))
    dest = tmp_path / "sub" / "file.csv"
    client = httpx.Client()
    try:
        out = download_csv_file(url, dest, client)
    finally:
        client.close()
    assert out.exists()
    assert out.read_text() == csv


def test_fetch_data_range_tzaware(tmp_path: Path):
    # tz-aware timestamps via trailing Z
    p = tmp_path / "tz.csv"
    p.write_text(
        "time,value\n"
        "2024-01-01T00:00:00Z,1\n"
        "2024-01-02T00:00:00Z,2\n"
        "2024-01-03T00:00:00Z,3\n"
    )
    cfg = APIConfig()
    df = fetch_data_range(
        config=cfg,
        urls=["http://unused"],
        cache_paths=[p],
        timestamp_col="time",
        start=pd.Timestamp("2024-01-02"),
        end=pd.Timestamp("2024-01-03"),
    )
    assert not df.empty
    # Normalize for comparison irrespective of tz-awareness
    idx_min = df.index.min()
    idx_max = df.index.max()
    if getattr(df.index, "tz", None) is not None:
        idx_min = idx_min.tz_convert(None)
        idx_max = idx_max.tz_convert(None)
    assert idx_min >= pd.Timestamp("2024-01-02")
    assert idx_max <= pd.Timestamp("2024-01-03")


