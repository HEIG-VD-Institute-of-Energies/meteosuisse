from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from ..config import APIConfig


@dataclass(slots=True)
class RadarDataConfig:
    precipitation_radar: str = "ch.meteoschweiz.ogd-radar-precipitation"
    hail_radar: str = "ch.meteoschweiz.ogd-radar-hail"
    reflectivity_radar: Optional[str] = None


class RadarData:
    def __init__(self, config: APIConfig):
        self._config = config
        self.collections = RadarDataConfig()


