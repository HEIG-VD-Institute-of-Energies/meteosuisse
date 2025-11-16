from pathlib import Path
import respx
import httpx
import pandas as pd
from meteosuisse.data_fetcher import fetch_data_range
from meteosuisse.config import APIConfig


@respx.mock
def test_fetch_data_range_triggers_download(tmp_path: Path):
    url = "https://example.com/a.csv"
    csv = "time,value\n2024-01-01T00:00:00,1\n"
    respx.get(url).mock(return_value=httpx.Response(200, text=csv))
    cache = tmp_path / "cache.csv"
    assert not cache.exists()
    cfg = APIConfig()
    df = fetch_data_range(
        config=cfg,
        urls=[url],
        cache_paths=[cache],
        timestamp_col="time",
        start=None,
        end=None,
    )
    assert cache.exists()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


