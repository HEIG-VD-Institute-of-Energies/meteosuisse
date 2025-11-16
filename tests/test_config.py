import httpx

from meteosuisse.config import APIConfig, TimeGranularity, UpdateFrequency


def test_time_granularity_enum_values():
    assert TimeGranularity.HOURLY.value == "h"
    assert TimeGranularity.DAILY.value == "d"
    assert TimeGranularity.MONTHLY.value == "m"


def test_update_frequency_enum_values():
    assert UpdateFrequency.NOW.value == "now"
    assert UpdateFrequency.RECENT.value == "recent"
    assert UpdateFrequency.HISTORICAL.value == "historical"


def test_api_config_headers_and_timeout_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = APIConfig(timeout_s=5.0, user_agent="UA")
    assert isinstance(cfg.httpx_timeout(), httpx.Timeout)
    limits = cfg.httpx_limits()
    assert isinstance(limits, httpx.Limits)
    assert cfg.headers()["User-Agent"] == "UA"
    # data/logs dirs created under CWD
    assert cfg.data_dir.exists()
    assert cfg.logs_dir.exists()
