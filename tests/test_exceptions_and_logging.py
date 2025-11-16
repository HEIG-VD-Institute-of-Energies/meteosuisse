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


def test_generic_httpx_error_is_mapped(monkeypatch):
    cfg = APIConfig()
    http = HttpClient(cfg)

    def _transport_error(path, params=None):
        raise httpx.TransportError("network down")

    monkeypatch.setattr(http._client, "get", _transport_error)  # type: ignore[attr-defined]
    with pytest.raises(MeteoSwissAPIError):
        http.get_json("/any")
    http.close()


def test_setup_logging_creates_log_file(tmp_path: Path):
    setup_logging(app_name="meteosuisse_test", logs_dir=tmp_path)
    files = list(tmp_path.glob("*.log"))
    assert files, "Expected a log file to be created"

def test_setup_logging_default_dir(monkeypatch, tmp_path: Path):
    # Cover logs_dir None branch by using CWD logs path
    monkeypatch.chdir(tmp_path)
    setup_logging(app_name="default_dir_test")
    logs_dir = tmp_path / "artifacts" / "logs"
    assert logs_dir.exists()
    assert list(logs_dir.glob("*.log"))


