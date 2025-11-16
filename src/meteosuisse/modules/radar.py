from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config import APIConfig
from ..stac_client import STACClient


@dataclass(slots=True)
class RadarDataConfig:
    precipitation_radar: str = "ch.meteoschweiz.ogd-radar-precipitation"
    hail_radar: str = "ch.meteoschweiz.ogd-radar-hail"
    reflectivity_radar: Optional[str] = None


class RadarData:
    def __init__(self, config: APIConfig):
        self._config = config
        self.collections = RadarDataConfig()

    def list_precipitation_radar_items(self, *, start_iso: str, end_iso: str) -> list[dict]:
        stac = STACClient(self._config)
        try:
            return stac.search_items(
                collection_id=self.collections.precipitation_radar,
                datetime_range=f"{start_iso}/{end_iso}",
                limit=200,
            )
        finally:
            stac.close()
