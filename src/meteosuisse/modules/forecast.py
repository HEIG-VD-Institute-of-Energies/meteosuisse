from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from ..config import APIConfig
from ..stac_client import STACClient


@dataclass(slots=True)
class ForecastDataConfig:
    short_term_forecast: Optional[str] = None
    icon_ch1_eps: str = "ch.meteoschweiz.ogd-forecast-icon-ch1-eps"
    icon_ch2_eps: str = "ch.meteoschweiz.ogd-forecast-icon-ch2-eps"
    local_forecast: str = "ch.meteoschweiz.ogd-forecast-local"


class ForecastData:
    def __init__(self, config: APIConfig):
        self._config = config
        self.collections = ForecastDataConfig()

    def list_icon_ch1_eps_items(self, *, start_iso: str, end_iso: str) -> list[dict]:
        stac = STACClient(self._config)
        try:
            return stac.search_items(
                collection_id=self.collections.icon_ch1_eps,
                datetime_range=f"{start_iso}/{end_iso}",
                limit=200,
            )
        finally:
            stac.close()

    def list_icon_ch2_eps_items(self, *, start_iso: str, end_iso: str) -> list[dict]:
        stac = STACClient(self._config)
        try:
            return stac.search_items(
                collection_id=self.collections.icon_ch2_eps,
                datetime_range=f"{start_iso}/{end_iso}",
                limit=200,
            )
        finally:
            stac.close()

    def list_local_forecast_items(self, *, start_iso: str, end_iso: str) -> list[dict]:
        stac = STACClient(self._config)
        try:
            return stac.search_items(
                collection_id=self.collections.local_forecast,
                datetime_range=f"{start_iso}/{end_iso}",
                limit=200,
            )
        finally:
            stac.close()

