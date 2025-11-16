from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running directly from repo without editable install
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rich.console import Console  # noqa: E402

from meteosuisse.config import APIConfig, TimeGranularity, UpdateFrequency  # noqa: E402
from meteosuisse.logging_setup import setup_logging  # noqa: E402
from meteosuisse.main_client import MeteoSwissClient  # noqa: E402


def main() -> None:
    setup_logging(app_name="meteosuisse_example")
    console = Console()
    client = MeteoSwissClient()

    # Yverdon-les-Bains closest station is Payerne's one.
    station_id = "GVE"

    # Date range: one year ago to now (UTC)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365)

    console.print(
        f"[bold]Fetching[/bold] Yverdon-les-Bains ({station_id}) "
        f"from {start.date()} to {end.date()} (hourly, recent)..."
    )

    df = client.ground_based.get_automatic_weather_stations(
        station_id=station_id,
        granularity=TimeGranularity.HOURLY,
        frequency=UpdateFrequency.RECENT,
        start=start,
        end=end,
    )

    if df.empty:
        console.print(
            f"[red]No data found for station {station_id} in the requested date range.[/red]"
        )
        return

    console.print(f"[green]Fetched {len(df)} hourly records[/green]")
    console.print(df.head())

    # Save to artifacts/outputs
    out_dir = APIConfig().artifacts_outputs_dir
    out_path = out_dir / "yverdon_last_year.csv"
    df.to_csv(out_path)
    console.print(f"[green]Saved[/green] CSV to {out_path}")


if __name__ == "__main__":
    main()
