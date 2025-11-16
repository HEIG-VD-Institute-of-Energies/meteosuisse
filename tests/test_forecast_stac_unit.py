import httpx
import respx
from meteosuisse.main_client import MeteoSwissClient


@respx.mock
def test_forecast_list_icon_ch1_items():
    """Test listing ICON CH1 EPS forecast items."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {"features": [{"id": "fc1"}], "links": []}
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    items = client.forecast.list_icon_ch1_eps_items(
        start_iso="2024-01-01T00:00:00Z",
        end_iso="2024-01-02T00:00:00Z",
    )
    assert isinstance(items, list)
    assert items and items[0]["id"] == "fc1"


@respx.mock
def test_forecast_list_icon_ch2_items():
    """Test listing ICON CH2 EPS forecast items."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {"features": [{"id": "fc2"}], "links": []}
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    items = client.forecast.list_icon_ch2_eps_items(
        start_iso="2024-01-01T00:00:00Z",
        end_iso="2024-01-02T00:00:00Z",
    )
    assert isinstance(items, list)
    assert items and items[0]["id"] == "fc2"


@respx.mock
def test_forecast_list_local_forecast_items():
    """Test listing local forecast items."""
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {"features": [{"id": "loc1"}], "links": []}
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    items = client.forecast.list_local_forecast_items(
        start_iso="2024-01-01T00:00:00Z",
        end_iso="2024-01-02T00:00:00Z",
    )
    assert isinstance(items, list)
    assert items and items[0]["id"] == "loc1"


