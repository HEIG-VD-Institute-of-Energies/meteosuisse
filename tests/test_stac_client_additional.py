"""Additional STAC client tests for coverage."""

from unittest.mock import MagicMock, patch

import pytest

from meteosuisse.config import APIConfig
from meteosuisse.stac_client import STACClient


@pytest.mark.unit
@patch("meteosuisse.stac_client.httpx.Client")
def test_stac_client_list_collections(mock_client_class):
    """Test list_collections method (lines 27-29)."""
    config = APIConfig()

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "collections": [{"id": "collection1"}, {"id": "collection2"}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    stac = STACClient(config)
    result = stac.list_collections()

    assert len(result) == 2
    assert result[0]["id"] == "collection1"
    mock_client.get.assert_called_once_with("/collections")
    stac.close()


@pytest.mark.unit
@patch("meteosuisse.stac_client.httpx.Client")
def test_stac_client_get_collection(mock_client_class):
    """Test get_collection method (lines 32-34)."""
    config = APIConfig()

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "collection1", "title": "Test Collection"}
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client

    stac = STACClient(config)
    result = stac.get_collection("collection1")

    assert result["id"] == "collection1"
    assert result["title"] == "Test Collection"
    mock_client.get.assert_called_once_with("/collections/collection1")
    stac.close()
