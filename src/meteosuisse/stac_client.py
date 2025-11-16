from __future__ import annotations

from typing import Any, Iterable, List
import httpx
from .config import APIConfig


class STACClient:
    """Minimal STAC client for MeteoSwiss data.geo.admin.ch."""

    def __init__(self, config: APIConfig | None = None) -> None:
        self._config = config or APIConfig()
        self._client = httpx.Client(
            timeout=self._config.httpx_timeout(),
            limits=self._config.httpx_limits(),
            headers=self._config.headers(),
            follow_redirects=True,
            http2=False,
            trust_env=False,
            base_url=self._config.base_url,
        )

    def close(self) -> None:
        self._client.close()

    def list_collections(self) -> list[dict]:
        r = self._client.get("/collections")
        r.raise_for_status()
        return r.json().get("collections", [])

    def get_collection(self, collection_id: str) -> dict:
        r = self._client.get(f"/collections/{collection_id}")
        r.raise_for_status()
        return r.json()

    def search_items(
        self,
        *,
        collection_id: str,
        datetime_range: str | None = None,
        ids: list[str] | None = None,
        query: dict[str, Any] | None = None,
        limit: int = 200,
    ) -> List[dict]:
        """POST /search for items in a collection.

        Args:
            collection_id: STAC collection ID
            datetime_range: Optional datetime range 'startZ/endZ' (ISO-8601). Note: For MeteoSwiss,
                items represent stations, not time periods, so datetime filtering may return empty.
            ids: Optional list of item IDs (station codes) to filter by. Case-insensitive matching.
            query: Optional STAC query object for property filtering
            limit: Maximum number of items to return per page
        """
        features: List[dict[str, Any]] = []
        payload: dict[str, Any] = {
            "collections": [collection_id],
            "limit": limit,
        }
        if datetime_range:
            payload["datetime"] = datetime_range
        if ids:
            # STAC API supports filtering by item IDs (case-sensitive, item IDs are lowercase)
            payload["ids"] = [i.lower() for i in ids]
        if query:
            payload["query"] = query

        r = self._client.post("/search", json=payload)
        r.raise_for_status()
        data = r.json()
        features.extend(data.get("features", []))

        # If ids provided but not found, try case-insensitive matching
        if ids and len(features) == 0:
            # Fetch all items and filter client-side
            payload_no_ids = {k: v for k, v in payload.items() if k != "ids"}
            r2 = self._client.post("/search", json=payload_no_ids)
            r2.raise_for_status()
            data2 = r2.json()
            all_items = data2.get("features", [])
            ids_lower = [i.lower() for i in ids]
            features = [item for item in all_items if item.get("id", "").lower() in ids_lower]

        # Follow pagination if present (only if not using ids filter and limit allows)
        # For performance, only paginate if we haven't reached the requested limit
        if not ids and len(features) < limit:
            next_link = None
            for link in data.get("links", []):
                if link.get("rel") == "next" and link.get("href"):
                    next_link = link["href"]
                    break
            # Limit pagination to avoid timeouts (max 3 pages = ~600 items)
            max_pages = 3
            page_count = 0
            while next_link and page_count < max_pages and len(features) < limit:
                r2 = self._client.get(next_link)
                r2.raise_for_status()
                data2 = r2.json()
                features.extend(data2.get("features", []))
                page_count += 1
                next_link = None
                for link in data2.get("links", []):
                    if link.get("rel") == "next" and link.get("href"):
                        next_link = link["href"]
                        break

        return features

    def list_station_ids(self, collection_id: str) -> list[str]:
        """List all station IDs (item IDs) in a collection."""
        items = self.search_items(collection_id=collection_id, limit=1000)
        return [item.get("id", "") for item in items if item.get("id")]

    def get_station_item(self, collection_id: str, station_id: str) -> dict | None:
        """Get STAC item for a specific station (case-insensitive)."""
        # Normalize to lowercase (STAC item IDs are lowercase)
        items = self.search_items(collection_id=collection_id, ids=[station_id.lower()])
        if items:
            return items[0]
        return None


