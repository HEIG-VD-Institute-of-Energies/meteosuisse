import httpx
import respx
import pytest
from meteosuisse.main_client import MeteoSwissClient


@respx.mock
def test_atmosphere_list_radio_soundings_items():
    """Test listing radio soundings items via STAC API."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {"features": [{"id": "snd1"}], "links": []}
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    items = client.atmosphere.list_radio_soundings_items(
        start_iso="2024-01-01T00:00:00Z",
        end_iso="2024-01-02T00:00:00Z",
        collection_id="ch.meteoschweiz.ogd-radiosoundings",  # hypothetical
    )
    assert isinstance(items, list)
    assert items and items[0]["id"] == "snd1"


def test_atmosphere_get_radio_soundings_not_implemented():
    """Test that get_radio_soundings raises NotImplementedError."""
    client = MeteoSwissClient()
    with pytest.raises(NotImplementedError, match="Radio soundings data will be available Q1-2026"):
        client.atmosphere.get_radio_soundings()


