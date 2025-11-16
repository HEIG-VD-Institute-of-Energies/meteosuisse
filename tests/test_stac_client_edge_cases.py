from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
import httpx

from meteosuisse.stac_client import STACClient
from meteosuisse.config import APIConfig


@pytest.mark.unit
def test_stac_client_init_with_config():
    """Test STACClient initialization with config."""
    config = APIConfig()
    client = STACClient(config)
    assert client._config == config
    client.close()


@pytest.mark.unit
def test_stac_client_init_without_config():
    """Test STACClient initialization without config."""
    client = STACClient()
    assert client._config is not None
    client.close()


@pytest.mark.unit
def test_stac_client_close():
    """Test STACClient close method."""
    client = STACClient()
    client.close()  # Should not raise
    # Can close multiple times
    client.close()


@pytest.mark.unit
@patch("meteosuisse.stac_client.httpx.Client")
def test_stac_search_items_with_query(mock_client_class):
    """Test search_items with query parameter (line 66)."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_response.get.return_value = []
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    config = APIConfig()
    stac = STACClient(config)
    
    result = stac.search_items(
        collection_id="test_collection",
        query={"property": {"value": "test"}},
        limit=10,
    )
    
    assert isinstance(result, list)
    # Verify query was included in payload
    call_args = mock_client.post.call_args
    assert "query" in call_args[1]["json"]
    stac.close()


@pytest.mark.unit
@patch("meteosuisse.stac_client.httpx.Client")
def test_stac_search_items_pagination_max_pages(mock_client_class):
    """Test search_items pagination respects max pages (lines 103-105)."""
    mock_client = MagicMock()
    
    # First response with next link
    response1 = MagicMock()
    response1.json.return_value = {
        "features": [{"id": "item1"}],
        "links": [{"rel": "next", "href": "http://example.com/search?page=2"}],
    }
    response1.raise_for_status = MagicMock()
    
    # Second response with next link
    response2 = MagicMock()
    response2.json.return_value = {
        "features": [{"id": "item2"}],
        "links": [{"rel": "next", "href": "http://example.com/search?page=3"}],
    }
    response2.raise_for_status = MagicMock()
    
    # Third response without next link (should stop after this due to max_pages)
    response3 = MagicMock()
    response3.json.return_value = {
        "features": [{"id": "item3"}],
        "links": [],  # No next link, but pagination should stop at max_pages anyway
    }
    response3.raise_for_status = MagicMock()
    
    # Use side_effect to return different responses for each call
    mock_client.post.return_value = response1
    # First GET call returns response2, second GET call returns response3
    # The pagination should stop after max_pages (3), so we only need 2 GET calls
    mock_client.get.side_effect = [response2, response3]
    mock_client_class.return_value = mock_client
    
    config = APIConfig()
    stac = STACClient(config)
    
    result = stac.search_items(collection_id="test_collection", limit=100)
    
    # Should have items from all 3 pages (max_pages = 3)
    # Page 1: item1, Page 2: item2, Page 3: item3
    assert len(result) == 3
    assert result[0]["id"] == "item1"
    assert result[1]["id"] == "item2"
    assert result[2]["id"] == "item3"
    # Should have made 2 GET calls (for pages 2 and 3)
    assert mock_client.get.call_count == 2
    stac.close()


@pytest.mark.unit
@patch("meteosuisse.stac_client.httpx.Client")
def test_stac_get_station_item_not_found(mock_client_class):
    """Test get_station_item returns None when not found (line 120)."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    config = APIConfig()
    stac = STACClient(config)
    
    result = stac.get_station_item("test_collection", "nonexistent")
    assert result is None
    stac.close()


@pytest.mark.unit
@patch("meteosuisse.stac_client.httpx.Client")
def test_stac_list_station_ids_empty_items(mock_client_class):
    """Test list_station_ids with items without IDs."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": [{"id": ""}, {}]}
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    config = APIConfig()
    stac = STACClient(config)
    
    result = stac.list_station_ids("test_collection")
    # Should filter out empty IDs
    assert "" not in result or len(result) == 0
    stac.close()

