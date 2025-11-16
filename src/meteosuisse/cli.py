from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import math

from shapely import wkt
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .main_client import MeteoSwissClient
from .config import TimeGranularity, UpdateFrequency, APIConfig
from .stac_client import STACClient
from .logging_setup import setup_logging


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (km)."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_station(
    stac_client: STACClient,
    collection_id: str,
    lat: float,
    lon: float,
    console: Console,
    max_stations: int = 500,
) -> Optional[tuple[str, float]]:
    """Find nearest station to given coordinates using Haversine distance.
    
    Args:
        stac_client: STAC client instance
        collection_id: STAC collection ID
        lat: Latitude
        lon: Longitude
        console: Rich console for output
        max_stations: Maximum number of stations to check (default: 500)
    
    Returns:
        Tuple of (station_id, distance_km) or None if no stations found.
    """
    console.print(f"[dim]Searching for nearest station in {collection_id}...[/dim]")
    
    # Fetch stations (limit to avoid timeout - use reasonable default)
    items = stac_client.search_items(collection_id=collection_id, limit=min(max_stations, 200))
    if not items:
        console.print("[yellow]No stations found in collection[/yellow]")
        return None
    
    console.print(f"[dim]Checking {len(items)} stations...[/dim]")
    
    nearest_station = None
    min_distance = float("inf")
    
    for item in items:
        geometry = item.get("geometry")
        if not geometry or geometry.get("type") != "Point":
            continue
        
        coords = geometry.get("coordinates", [])
        if len(coords) != 2:
            continue
        
        station_lon, station_lat = coords[0], coords[1]
        distance = haversine_distance(lat, lon, station_lat, station_lon)
        
        if distance < min_distance:
            min_distance = distance
            nearest_station = item.get("id", "").upper()
    
    if nearest_station:
        console.print(f"[green]Found nearest station: {nearest_station} ({min_distance:.2f} km away)[/green]")
        return (nearest_station, min_distance)
    
    console.print("[yellow]No valid station geometries found[/yellow]")
    return None


def parse_geometry_input(geometry_input: str) -> Optional[tuple[float, float]]:
    """Parse geometry input (GeoJSON, WKT, or lat,lon string).
    
    Supports Points, Polygons, MultiPolygons, and other geometries.
    For non-point geometries, extracts the centroid.
    
    Args:
        geometry_input: Geometry as:
            - lat,lon string (e.g., "46.247519,6.127742")
            - GeoJSON string (Point, Polygon, MultiPolygon, Feature)
            - WKT string (POINT, POLYGON, MULTIPOLYGON, etc.)
            - Path to GeoJSON file
    
    Returns:
        Tuple of (lat, lon) representing the point or centroid, or None if parsing fails.
    """
    # Try as lat,lon string (simple case)
    if "," in geometry_input and not geometry_input.strip().startswith(("{", "POINT", "POLYGON", "MULTI")):
        try:
            parts = geometry_input.split(",")
            if len(parts) == 2:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                # Basic validation: lat should be -90 to 90, lon -180 to 180
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
        except ValueError:
            pass
    
    # Try as GeoJSON string
    try:
        geo = json.loads(geometry_input)
        geom = None
        
        # Handle Feature objects
        if geo.get("type") == "Feature":
            geom_dict = geo.get("geometry")
            if geom_dict:
                geom = shape(geom_dict)
        # Handle Geometry objects directly
        elif geo.get("type") in ("Point", "Polygon", "MultiPolygon", "LineString", "MultiLineString"):
            geom = shape(geo)
        
        if geom:
            if isinstance(geom, Point):
                return (geom.y, geom.x)  # GeoJSON is [lon, lat], return (lat, lon)
            else:
                # For polygons and other geometries, use centroid
                centroid = geom.centroid
                return (centroid.y, centroid.x)
    except (json.JSONDecodeError, KeyError, Exception):
        pass
    
    # Try as WKT string (handles POINT, POLYGON, MULTIPOLYGON, etc.)
    try:
        geom = wkt.loads(geometry_input)
        if isinstance(geom, Point):
            return (geom.y, geom.x)  # WKT is (lon, lat), return (lat, lon)
        else:
            # For polygons and other geometries, use centroid
            centroid = geom.centroid
            return (centroid.y, centroid.x)
    except Exception:
        pass
    
    # Try as file path (GeoJSON)
    geo_path = Path(geometry_input)
    if geo_path.exists():
        try:
            geo = json.loads(geo_path.read_text())
            geom = None
            
            if geo.get("type") == "Feature":
                geom_dict = geo.get("geometry")
                if geom_dict:
                    geom = shape(geom_dict)
            elif geo.get("type") in ("Point", "Polygon", "MultiPolygon", "LineString", "MultiLineString"):
                geom = shape(geo)
            
            if geom:
                if isinstance(geom, Point):
                    return (geom.y, geom.x)
                else:
                    centroid = geom.centroid
                    return (centroid.y, centroid.x)
        except (json.JSONDecodeError, KeyError, IOError, Exception):
            pass
    
    return None


def resolve_station_id(
    client: MeteoSwissClient,
    station_id: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
    geometry: Optional[str],
    data_type: str,
    console: Console,
) -> Optional[str]:
    """Resolve station ID from various input formats.
    
    Args:
        client: MeteoSwiss client
        station_id: Direct station code
        lat: Latitude
        lon: Longitude
        geometry: Geometry string (GeoJSON, WKT, or lat,lon)
        data_type: Data type ("ground" or "climate")
        console: Rich console for output
    
    Returns:
        Station ID or None if resolution fails.
    """
    if station_id:
        return station_id.upper()
    
    # Determine collection ID based on data type
    if data_type == "ground":
        collection_id = "ch.meteoschweiz.ogd-smn"
    elif data_type == "climate":
        collection_id = "ch.meteoschweiz.ogd-climate-homogeneous"
    else:
        console.print(f"[red]Unknown data type: {data_type}[/red]")
        return None
    
    # Parse geometry if provided
    if geometry:
        coords = parse_geometry_input(geometry)
        if coords:
            lat, lon = coords
        else:
            console.print(f"[yellow]Warning: Could not parse geometry '{geometry}', ignoring[/yellow]")
            geometry = None
    
    # Use lat/lon if provided
    if lat is not None and lon is not None:
        stac = STACClient(client.config)
        try:
            result = find_nearest_station(stac, collection_id, lat, lon, console)
            if result:
                return result[0]
            else:
                console.print("[red]No stations found near the specified location[/red]")
                return None
        finally:
            stac.close()
    
    console.print("[red]Error: Must provide either --station-id, --lat/--lon, or --geometry[/red]")
    return None


def parse_date(date_str: str) -> datetime:
    """Parse date string (ISO format or YYYY-MM-DD)."""
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=None)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use ISO format or YYYY-MM-DD")


def main() -> None:
    """CLI entry point for fetching MeteoSwiss weather data."""
    parser = argparse.ArgumentParser(
        description="Fetch MeteoSwiss weather data and export to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch by station code
  %(prog)s --station-id GVE --start 2024-01-01 --end 2024-12-31
  
  # Fetch by coordinates
  %(prog)s --lat 46.247519 --lon 6.127742 --start 2024-01-01 --end 2024-12-31
  
  # Fetch climate data
  %(prog)s --station-id GEN --data-type climate --granularity daily --start 2024-01-01
  
  # Fetch with geometry (GeoJSON)
  %(prog)s --geometry '{"type":"Point","coordinates":[6.127742,46.247519]}' --start 2024-01-01
        """,
    )
    
    # Location options (mutually exclusive group)
    location_group = parser.add_mutually_exclusive_group(required=True)
    location_group.add_argument(
        "--station-id",
        type=str,
        help="Weather station code (e.g., GVE, BER, GEN)",
    )
    location_group.add_argument(
        "--lat",
        type=float,
        metavar="LATITUDE",
        help="Latitude (use with --lon to find nearest station)",
    )
    location_group.add_argument(
        "--geometry",
        type=str,
        metavar="GEOMETRY",
        help="Geometry as GeoJSON string, WKT POINT, lat,lon string, or path to GeoJSON file",
    )
    
    parser.add_argument(
        "--lon",
        type=float,
        metavar="LONGITUDE",
        help="Longitude (use with --lat to find nearest station)",
    )
    
    # Date options
    parser.add_argument(
        "--start",
        type=parse_date,
        help="Start date (ISO format or YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=parse_date,
        help="End date (ISO format or YYYY-MM-DD). Defaults to now if not specified.",
    )
    
    # Data type options
    parser.add_argument(
        "--data-type",
        choices=["ground", "climate"],
        default="ground",
        help="Data type: ground-based automatic weather stations or climate homogeneous series (default: ground)",
    )
    
    parser.add_argument(
        "--granularity",
        choices=["t", "h", "d", "m", "y"],
        default="h",
        help="Time granularity: t=10min, h=hourly, d=daily, m=monthly, y=yearly (default: h)",
    )
    
    parser.add_argument(
        "--frequency",
        choices=["now", "recent", "historical"],
        default="recent",
        help="Update frequency: now, recent, or historical (default: recent)",
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        metavar="PATH",
        help="Output CSV file path (default: artifacts/outputs/weather_data.csv)",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(app_name="meteosuisse_cli")
    console = Console()
    
    # Validate lat/lon pair
    if args.lat is not None and args.lon is None:
        parser.error("--lon is required when --lat is specified")
    if args.lon is not None and args.lat is None:
        parser.error("--lat is required when --lon is specified")
    
    # Initialize client
    client = MeteoSwissClient()
    
    # Resolve station ID
    station_id = resolve_station_id(
        client=client,
        station_id=args.station_id,
        lat=args.lat,
        lon=args.lon,
        geometry=args.geometry,
        data_type=args.data_type,
        console=console,
    )
    
    if not station_id:
        console.print("[red]Failed to resolve station ID[/red]")
        return 1
    
    # Parse granularity and frequency
    gran_map = {
        "t": TimeGranularity.TEN_MINUTES,
        "h": TimeGranularity.HOURLY,
        "d": TimeGranularity.DAILY,
        "m": TimeGranularity.MONTHLY,
        "y": TimeGranularity.YEARLY,
    }
    granularity = gran_map[args.granularity]
    
    freq_map = {
        "now": UpdateFrequency.NOW,
        "recent": UpdateFrequency.RECENT,
        "historical": UpdateFrequency.HISTORICAL,
    }
    frequency = freq_map[args.frequency]
    
    # Parse dates
    end = args.end
    if end and end.tzinfo is None:
        from datetime import timezone
        end = end.replace(tzinfo=timezone.utc)
    elif not end:
        from datetime import timezone
        end = datetime.now(timezone.utc)
    
    start = args.start
    if start and start.tzinfo is None:
        from datetime import timezone
        start = start.replace(tzinfo=timezone.utc)
    
    # Display request summary
    summary_table = Table(title="Request Summary", show_header=True, header_style="bold")
    summary_table.add_column("Parameter")
    summary_table.add_column("Value")
    summary_table.add_row("Station ID", station_id)
    summary_table.add_row("Data Type", args.data_type)
    summary_table.add_row("Granularity", args.granularity)
    summary_table.add_row("Frequency", args.frequency)
    summary_table.add_row("Start Date", start.isoformat() if start else "Not specified")
    summary_table.add_row("End Date", end.isoformat())
    
    console.print(Panel(summary_table, title="[bold]Fetching Weather Data[/bold]", border_style="green"))
    
    # Fetch data
    try:
        if args.data_type == "ground":
            df = client.ground_based.get_automatic_weather_stations(
                station_id=station_id,
                granularity=granularity,
                frequency=frequency,
                start=start,
                end=end,
            )
        elif args.data_type == "climate":
            df = client.climate.get_homogeneous_series(
                station_id=station_id,
                granularity=granularity,
                start=start,
                end=end,
            )
        else:
            console.print(f"[red]Unknown data type: {args.data_type}[/red]")
            return 1
        
        if df.empty:
            console.print(f"[yellow]No data found for station {station_id} in the requested date range[/yellow]")
            return 1
        
        # Display data summary
        console.print(f"[green]✓[/green] Fetched [bold]{len(df)}[/bold] records")
        console.print(f"[dim]Date range: {df.index.min()} to {df.index.max()}[/dim]")
        console.print(f"[dim]Columns: {', '.join(df.columns[:5].tolist())}{'...' if len(df.columns) > 5 else ''}[/dim]")
        
        # Save to CSV
        if args.output:
            output_path = args.output
        else:
            cfg = APIConfig()
            output_path = cfg.artifacts_outputs_dir / f"weather_data_{station_id}_{args.granularity}.csv"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path)
        console.print(f"[green]✓[/green] Saved CSV to [bold]{output_path}[/bold]")
        
        return 0
        
    except Exception as e:
        console.print(f"[red]Error fetching data: {e}[/red]")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

