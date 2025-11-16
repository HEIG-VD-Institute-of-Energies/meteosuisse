from __future__ import annotations

from rich.console import Console
from rich.table import Table
from meteosuisse.logging_setup import setup_logging
from meteosuisse.main_client import MeteoSwissClient


def main() -> None:
    setup_logging(app_name="meteosuisse_cli")
    console = Console()
    client = MeteoSwissClient()
    cols = client.list_collections()
    table = Table(title="MeteoSwiss STAC Collections")
    table.add_column("ID")
    table.add_column("Title", overflow="fold")
    for c in cols[:10]:
        table.add_row(str(c.get("id", "")), str(c.get("title", "")))
    console.print(table)
    console.print(f"[green]Total collections:[/green] {len(cols)}")


if __name__ == "__main__":
    main()


