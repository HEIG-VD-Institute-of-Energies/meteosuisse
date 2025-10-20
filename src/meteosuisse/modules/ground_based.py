from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
from ..config import APIConfig, TimeGranularity, UpdateFrequency
from ..client import HttpClient
from ..data_fetcher import fetch_data_range


@dataclass(slots=True)
class GroundBasedMeasurementsConfig:
    automatic_weather_stations: str = "ch.meteoschweiz.ogd-smn"
    automatic_precipitation: str = "ch.meteoschweiz.ogd-smn-precip"
    automatic_tower: str = "ch.meteoschweiz.ogd-smn-tower"
    automatic_soil_moisture: Optional[str] = None
    manual_precipitation: str = "ch.meteoschweiz.ogd-nime"
    totaliser_precipitation: str = "ch.meteoschweiz.ogd-tot"
    pollen: str = "ch.meteoschweiz.ogd-pollen"
    visual_observations: str = "ch.meteoschweiz.ogd-obs"
    phenology: str = "ch.meteoschweiz.ogd-phenology"


class GroundBasedMeasurements:
    def __init__(self, config: APIConfig):
        self._config = config
        self._http = HttpClient(config)
        self.collections = GroundBasedMeasurementsConfig()

    def _collection_info(self, collection_id: str) -> dict:
        return self._http.get_json(f"/collections/{collection_id}")

    def get_automatic_weather_stations(
        self,
        *,
        station_id: Optional[str] = None,
        granularity: TimeGranularity = TimeGranularity.HOURLY,
        frequency: UpdateFrequency = UpdateFrequency.RECENT,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> pd.DataFrame:
        _ = self._collection_info(self.collections.automatic_weather_stations)
        # Placeholder: actual file URLs would be resolved via STAC assets; here we leave structure ready
        urls: list[str] = []
        cache_paths: list[Path] = []
        return fetch_data_range(
            config=self._config,
            urls=urls,
            cache_paths=cache_paths,
            timestamp_col="time",
            start=start,
            end=end,
        )


