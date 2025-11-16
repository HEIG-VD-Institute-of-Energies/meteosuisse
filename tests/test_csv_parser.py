from pathlib import Path

import pandas as pd

from meteosuisse.csv_parser import (
    parse_data_inventory_csv,
    parse_measurement_data_csv,
    parse_parameters_csv,
    parse_stations_csv,
)


def test_parse_simple_csvs(tmp_path: Path):
    stations = tmp_path / "stations.csv"
    stations.write_text("identifier,name\nBER,Bern\n")
    params = tmp_path / "params.csv"
    params.write_text("identifier,description,time_interval\np,Precip,h\n")
    inv = tmp_path / "inv.csv"
    inv.write_text("station_id,parameter_id,start_date,end_date\nBER,p,2020-01-01,2020-01-31\n")

    df_s = parse_stations_csv(stations)
    df_p = parse_parameters_csv(params)
    df_i = parse_data_inventory_csv(inv)

    assert list(df_s.columns) == ["identifier", "name"]
    assert df_p.loc[0, "time_interval"] == "h"
    assert pd.api.types.is_datetime64_any_dtype(df_i["start_date"])


def test_parse_measurement_data_csv_sets_index(tmp_path: Path):
    data = tmp_path / "data.csv"
    data.write_text("time,value\n2024-01-01T00:00:00,1.0\n2024-01-01T01:00:00,2.0\n")
    df = parse_measurement_data_csv(data, timestamp_col="time")
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.is_monotonic_increasing
    assert "value" in df.columns
