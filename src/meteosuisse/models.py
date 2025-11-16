from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Station:
    identifier: str
    name: str
    canton: Optional[str] = None
    wigos_id: Optional[str] = None
    station_type: Optional[str] = None
    altitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    orientation: Optional[str] = None
    url: Optional[str] = None


@dataclass(slots=True)
class Parameter:
    identifier: str
    description: str
    time_interval: str
    decimal_places: Optional[int] = None
    data_type: Optional[str] = None
    unit: Optional[str] = None


@dataclass(slots=True)
class DataInventory:
    station_id: str
    parameter_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass(slots=True)
class CollectionMetadata:
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    links: list[dict] = field(default_factory=list)
