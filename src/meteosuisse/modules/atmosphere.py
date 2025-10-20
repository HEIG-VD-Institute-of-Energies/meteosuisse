from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from ..config import APIConfig


@dataclass(slots=True)
class AtmosphereMeasurementsConfig:
    radio_soundings: Optional[str] = None


class AtmosphereMeasurements:
    def __init__(self, config: APIConfig):
        self._config = config
        self.collections = AtmosphereMeasurementsConfig()

    def get_radio_soundings(self):
        raise NotImplementedError("Radio soundings data will be available Q1-2026")


