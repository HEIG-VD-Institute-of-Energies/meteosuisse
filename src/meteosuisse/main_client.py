from __future__ import annotations

from typing import Any

from .client import HttpClient
from .config import APIConfig
from .modules.atmosphere import AtmosphereMeasurements
from .modules.climate import ClimateData
from .modules.forecast import ForecastData
from .modules.ground_based import GroundBasedMeasurements
from .modules.radar import RadarData


class MeteoSwissClient:
    """Unified client for MeteoSwiss Open Data.

    Documentation: https://opendatadocs.meteoswiss.ch
    Attribution: "Source: MeteoSwiss"
    """

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig()
        self._http = HttpClient(self.config)
        self.ground_based = GroundBasedMeasurements(self.config)
        self.atmosphere = AtmosphereMeasurements(self.config)
        self.climate = ClimateData(self.config)
        self.radar = RadarData(self.config)
        self.forecast = ForecastData(self.config)

    def list_collections(self) -> list[dict[str, Any]]:
        return self._http.get_json("/collections").get("collections", [])

    def get_collection_info(self, collection_id: str) -> dict[str, Any]:
        return self._http.get_json(f"/collections/{collection_id}")
