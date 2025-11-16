from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config import APIConfig
from ..stac_client import STACClient


@dataclass(slots=True)
class AtmosphereMeasurementsConfig:
    radio_soundings: Optional[str] = None


class AtmosphereMeasurements:
    def __init__(self, config: APIConfig):
        self._config = config
        self.collections = AtmosphereMeasurementsConfig()

    def list_radio_soundings_items(
        self, *, start_iso: str, end_iso: str, collection_id: str
    ) -> list[dict]:
        """Generic listing for radio soundings collections if/when available."""
        stac = STACClient(self._config)
        try:
            dt_range = f"{start_iso}/{end_iso}"
            return stac.search_items(
                collection_id=collection_id, datetime_range=dt_range, limit=200
            )
        finally:
            stac.close()

    def get_radio_soundings(self):
        raise NotImplementedError("Radio soundings data will be available Q1-2026")
