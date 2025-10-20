from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import httpx


class TimeGranularity(str, Enum):
    TEN_MINUTES = "t"
    HOURLY = "h"
    DAILY = "d"
    MONTHLY = "m"
    YEARLY = "y"


class UpdateFrequency(str, Enum):
    NOW = "now"
    RECENT = "recent"
    HISTORICAL = "historical"


@dataclass(slots=True)
class APIConfig:
    base_url: str = "https://data.geo.admin.ch/api/stac/v1"
    file_base_url: str = "https://data.geo.admin.ch"
    timeout_s: float = 10.0
    user_agent: str = "MeteoSwiss-Python-Client/1.0"

    def httpx_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(self.timeout_s)

    def httpx_limits(self) -> httpx.Limits:
        return httpx.Limits(max_keepalive_connections=20, max_connections=100)

    def headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent, "Accept": "application/json"}

    @property
    def data_dir(self) -> Path:
        d = Path.cwd() / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def logs_dir(self) -> Path:
        d = Path.cwd() / "logs"
        d.mkdir(parents=True, exist_ok=True)
        return d


