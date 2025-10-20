from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from ..config import APIConfig


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


