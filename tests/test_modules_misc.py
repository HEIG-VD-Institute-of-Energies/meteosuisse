import pandas as pd
import pytest

from meteosuisse.main_client import MeteoSwissClient


def test_atmosphere_not_implemented():
    client = MeteoSwissClient()
    with pytest.raises(NotImplementedError):
        client.atmosphere.get_radio_soundings()


def test_climate_get_homogeneous_series_no_network(monkeypatch):
    client = MeteoSwissClient()
    # Avoid network by short-circuiting collection info
    monkeypatch.setattr(client.climate, "_collection_info", lambda x: {"id": x})
    df = client.climate.get_homogeneous_series()
    assert isinstance(df, pd.DataFrame)


def test_climate_collection_info_monkeypatched(monkeypatch):
    client = MeteoSwissClient()
    # Cover _collection_info helper
    called = {}

    def fake_get_json(path):
        called["path"] = path
        return {"ok": True}

    monkeypatch.setattr(client.climate._http, "get_json", lambda p: fake_get_json(p))
    info = client.climate._collection_info("abc")
    assert info == {"ok": True}
    assert "collections/abc" in called["path"]
