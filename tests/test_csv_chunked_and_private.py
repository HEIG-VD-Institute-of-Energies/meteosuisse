from pathlib import Path

import pandas as pd

from meteosuisse.csv_parser import _read_csv


def test_read_csv_chunked(tmp_path: Path):
    p = tmp_path / "big.csv"
    # 3 rows to force multiple chunks with chunksize=2
    p.write_text("time,value\n2024-01-01,1\n2024-01-02,2\n2024-01-03,3\n")
    df = _read_csv(p, parse_dates=["time"], chunksize=2)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert pd.api.types.is_datetime64_any_dtype(df["time"])
