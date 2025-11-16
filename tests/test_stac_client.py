import httpx
import respx

from meteosuisse.stac_client import STACClient


@respx.mock
def test_stac_search_items_pagination():
    base = "https://data.geo.admin.ch/api/stac/v1"

    first = {
        "features": [{"id": "a1"}],
        "links": [{"rel": "next", "href": f"{base}/search?next=token"}],
    }
    second = {
        "features": [{"id": "a2"}],
        "links": [],
    }

    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=first))
    respx.get(f"{base}/search?next=token").mock(return_value=httpx.Response(200, json=second))

    c = STACClient()
    try:
        # datetime_range is now optional
        feats = c.search_items(collection_id="ch.meteoschweiz.ogd-smn", limit=2)
    finally:
        c.close()

    assert len(feats) == 2
    assert feats[0]["id"] == "a1" and feats[1]["id"] == "a2"


@respx.mock
def test_stac_search_items_by_ids():
    base = "https://data.geo.admin.ch/api/stac/v1"

    search_json = {
        "features": [
            {"id": "gve"},
            {"id": "ber"},
        ],
        "links": [],
    }

    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    c = STACClient()
    try:
        feats = c.search_items(
            collection_id="ch.meteoschweiz.ogd-smn",
            ids=["GVE", "BER"],
            limit=10,
        )
    finally:
        c.close()

    assert len(feats) == 2
    assert {f["id"] for f in feats} == {"gve", "ber"}


@respx.mock
def test_stac_search_items_no_datetime():
    """Test that search works without datetime (items represent stations, not time periods)."""
    base = "https://data.geo.admin.ch/api/stac/v1"

    search_json = {
        "features": [{"id": "abo"}, {"id": "aeg"}],
        "links": [],
    }

    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    c = STACClient()
    try:
        feats = c.search_items(collection_id="ch.meteoschweiz.ogd-smn", limit=10)
    finally:
        c.close()

    assert len(feats) == 2


@respx.mock
def test_stac_list_station_ids():
    base = "https://data.geo.admin.ch/api/stac/v1"

    search_json = {
        "features": [
            {"id": "gve"},
            {"id": "ber"},
            {"id": "pay"},
        ],
        "links": [],
    }

    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    c = STACClient()
    try:
        station_ids = c.list_station_ids("ch.meteoschweiz.ogd-smn")
    finally:
        c.close()

    assert len(station_ids) == 3
    assert "gve" in station_ids
    assert "ber" in station_ids
    assert "pay" in station_ids


@respx.mock
def test_stac_get_station_item():
    base = "https://data.geo.admin.ch/api/stac/v1"

    search_json = {
        "features": [{"id": "gve", "properties": {"title": "Geneva"}}],
        "links": [],
    }

    respx.post(f"{base}/search").mock(return_value=httpx.Response(200, json=search_json))

    c = STACClient()
    try:
        item = c.get_station_item("ch.meteoschweiz.ogd-smn", "GVE")
    finally:
        c.close()

    assert item is not None
    assert item["id"] == "gve"
    assert item["properties"]["title"] == "Geneva"
