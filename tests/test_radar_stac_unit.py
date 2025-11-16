import httpx
import respx

from meteosuisse.main_client import MeteoSwissClient


@respx.mock
def test_radar_list_precipitation_items():
    base = "https://data.geo.admin.ch/api/stac/v1"
    search_json = {"features": [{"id": "rad1"}], "links": []}
    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    client = MeteoSwissClient()
    items = client.radar.list_precipitation_radar_items(
        start_iso="2024-01-01T00:00:00Z",
        end_iso="2024-01-02T00:00:00Z",
    )
    assert isinstance(items, list)
    assert items and items[0]["id"] == "rad1"
