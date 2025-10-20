from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
from ..config import APIConfig, TimeGranularity
from ..client import HttpClient
from ..data_fetcher import fetch_data_range


@dataclass(slots=True)
class ClimateDataConfig:
    climate_stations_homogeneous: str = "ch.meteoschweiz.ogd-climate-homogeneous"
    climate_precipitation_homogeneous: Optional[str] = None
    ground_based_spatial: Optional[str] = None
    satellite_based_spatial: Optional[str] = None
    radar_based_spatial: Optional[str] = None
    climate_normals: Optional[str] = None
    spatial_climate_normals: Optional[str] = None
    climate_scenarios_ch2025: Optional[str] = None
    spatial_climate_scenarios_ch2025: Optional[str] = None


class ClimateData:
    def __init__(self, config: APIConfig):
        self._config = config
        self._http = HttpClient(config)
        self.collections = ClimateDataConfig()

    def _collection_info(self, collection_id: str) -> dict:
        return self._http.get_json(f"/collections/{collection_id}")

    def get_homogeneous_series(
        self,
        *,
        station_id: Optional[str] = None,
        granularity: TimeGranularity = TimeGranularity.DAILY,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> pd.DataFrame:
        _ = self._collection_info(self.collections.climate_stations_homogeneous)
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


