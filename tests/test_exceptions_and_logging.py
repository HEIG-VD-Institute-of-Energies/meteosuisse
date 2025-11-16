from pathlib import Path
import pytest
import httpx
from meteosuisse.client import HttpClient
from meteosuisse.config import APIConfig
from meteosuisse.exceptions import MeteoSwissAPIError
from meteosuisse.logging_setup import setup_logging


def test_http_errors_are_mapped_to_custom_exception(monkeypatch):
    cfg = APIConfig()
    http = HttpClient(cfg)

    def _raise_status_error(path, params=None):
        req = httpx.Request("GET", cfg.base_url + path)
        resp = httpx.Response(404, request=req)
        raise httpx.HTTPStatusError("Not found", request=req, response=resp)

    # Monkeypatch the underlying client's get to raise
    monkeypatch.setattr(http._client, "get", _raise_status_error)  # type: ignore[attr-defined]
    with pytest.raises(MeteoSwissAPIError):
        http.get_json("/does-not-exist")
    http.close()


def test_setup_logging_creates_log_file(tmp_path: Path):
    setup_logging(app_name="meteosuisse_test", logs_dir=tmp_path)
    files = list(tmp_path.glob("*.log"))
    assert files, "Expected a log file to be created"


