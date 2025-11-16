from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
from io import StringIO
import httpx
from ..config import APIConfig, TimeGranularity
from ..client import HttpClient
from ..data_fetcher import fetch_data_range
from ..stac_client import STACClient


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
        """Get homogeneous climate series via STAC API.

        STAC items represent stations (not time periods), so we search by station ID
        in item IDs, then filter time ranges in the downloaded CSV data.
        """
        if not self.collections.climate_stations_homogeneous:
            return pd.DataFrame()
        passed_start = start
        passed_end = end

        # Map granularity to asset name patterns
        gran_map = {
            TimeGranularity.TEN_MINUTES: "t",
            TimeGranularity.HOURLY: "h",
            TimeGranularity.DAILY: "d",
            TimeGranularity.MONTHLY: "m",
            TimeGranularity.YEARLY: "y",
        }
        gran_char = gran_map.get(granularity, "d")

        stac = STACClient(self._config)
        try:
            # Search by station ID in item IDs (not datetime)
            if station_id:
                items = stac.search_items(
                    collection_id=self.collections.climate_stations_homogeneous,
                    ids=[station_id],
                    limit=10,
                )
            else:
                items = stac.search_items(
                    collection_id=self.collections.climate_stations_homogeneous,
                    limit=200,
                )
        except Exception:
            items = []
        finally:
            stac.close()

        if not items:
            return pd.DataFrame()

        # Determine if we need historical assets based on date range
        needs_historical = False
        relevant_decades: set[int] = set()
        if passed_start is not None:
            start_year = passed_start.year
            end_year = passed_end.year if passed_end else start_year
            current_year = pd.Timestamp.now(tz=passed_start.tzinfo if passed_start.tzinfo else None).year
            if start_year < current_year:
                needs_historical = True
                for year in range(start_year, min(end_year + 1, current_year + 1)):
                    decade_start = (year // 10) * 10
                    relevant_decades.add(decade_start)

        # Select CSV assets (prefer matching granularity, include historical if needed)
        urls: list[str] = []
        for feat in items:
            assets = feat.get("assets", {}) or {}
            for asset_key, asset in assets.items():
                href = str(asset.get("href", ""))
                atype = str(asset.get("type", ""))
                if not (href.lower().endswith(".csv") or "text/csv" in atype or "text/plain" in atype):
                    continue
                asset_lower = asset_key.lower()
                
                # Check if asset matches requested granularity
                # Pattern: climate_STATION_gran.csv or *_gran_*.csv
                matches_granularity = (
                    f"_{gran_char}_" in asset_lower
                    or asset_lower.endswith(f"_{gran_char}.csv")
                    or f"_{gran_char}." in asset_lower
                )
                
                if not matches_granularity:
                    continue
                
                # Include assets matching requested granularity
                urls.append(href)
                
                # Also include historical assets if date range requires them
                if needs_historical and "historical" in asset_lower:
                    for decade_start in relevant_decades:
                        decade_str = f"{decade_start}-{decade_start + 9}"
                        if decade_str in asset_lower:
                            if href not in urls:  # Avoid duplicates
                                urls.append(href)  # pragma: no cover
                            break

        if not urls:
            return pd.DataFrame()

        frames: list[pd.DataFrame] = []
        with httpx.Client(
            timeout=self._config.httpx_timeout(),
            limits=self._config.httpx_limits(),
            follow_redirects=True,
        ) as hc:
            for url in urls:
                try:
                    r = hc.get(url)
                    r.raise_for_status()
                    df = pd.read_csv(StringIO(r.text), sep=None, engine="python")
                    if df.empty:
                        continue
                    # Normalize time column - MeteoSwiss may use various formats
                    time_cols = ("reference_timestamp", "time", "timestamp", "date", "datetime")
                    time_col_found = False
                    for tcol in time_cols:
                        if tcol in df.columns:
                            # Try DD.MM.YYYY format first (MeteoSwiss format), then fallback to auto-detect
                            # Note: DD.MM.YYYY parsing creates timezone-naive datetimes (no timezone info in format)
                            # We'll localize to UTC later if needed (line 213)
                            parsed_ddmm = pd.to_datetime(
                                df[tcol],
                                format="%d.%m.%Y %H:%M",
                                errors="coerce",
                            )
                            # If DD.MM.YYYY format didn't work (all NaT), try auto-detection with UTC
                            if parsed_ddmm.isna().all():
                                df[tcol] = pd.to_datetime(df[tcol], errors="coerce", utc=True)
                            else:
                                df[tcol] = parsed_ddmm  # Timezone-naive, will be localized at line 213 if needed
                            # Remove rows with invalid timestamps
                            df = df[df[tcol].notna()]
                            if df.empty:
                                break
                            df = df.set_index(tcol).sort_index()
                            time_col_found = True
                            break
                    if not time_col_found:
                        continue
                    frames.append(df)
                except Exception:
                    continue

        if not frames:
            return pd.DataFrame()

        out = pd.concat(frames).sort_index()

        # Station filtering (if not already filtered at STAC level)
        # Climate data may use "station" or "station_id" column
        if station_id:
            sid = station_id.upper()
            matched = False
            for scol in ("station", "station_id", "stn", "stationname", "name", "station_code", "stationcode"):
                if scol in out.columns:
                    col = out[scol].astype(str).str.upper()
                    out = out[col.eq(sid)]
                    matched = True
                    break
            # If no explicit station column, try broad text search
            if not matched:
                obj_cols = [c for c in out.columns if out[c].dtype == "object"]
                if obj_cols:
                    mask = None
                    for c in obj_cols:
                        colu = out[c].astype(str).str.upper()
                        col_mask = colu.eq(sid) | colu.str.contains(fr"\b{sid}\b", regex=True)
                        mask = col_mask if mask is None else (mask | col_mask)
                    if mask is not None and mask.any():
                        out = out[mask]

        # Date range filtering
        if isinstance(out.index, pd.DatetimeIndex):
            # Ensure index is timezone-aware (UTC)
            if out.index.tz is None:
                out.index = out.index.tz_localize("UTC")
            else:
                out.index = out.index.tz_convert("UTC")
            
            out = out[out.index.notna()]
            if passed_start is not None:
                start_ts = pd.Timestamp(passed_start)
                if start_ts.tzinfo is None:
                    start_ts = start_ts.tz_localize("UTC")
                else:
                    start_ts = start_ts.tz_convert("UTC")
                out = out[out.index >= start_ts]
            if passed_end is not None:
                end_ts = pd.Timestamp(passed_end)
                if end_ts.tzinfo is None:
                    end_ts = end_ts.tz_localize("UTC")
                else:
                    end_ts = end_ts.tz_convert("UTC")
                out = out[out.index <= end_ts]
        
        # Remove duplicate index entries (keep last)
        if isinstance(out.index, pd.DatetimeIndex):
            out = out[~out.index.duplicated(keep="last")]
            out = out.sort_index()

        return out


