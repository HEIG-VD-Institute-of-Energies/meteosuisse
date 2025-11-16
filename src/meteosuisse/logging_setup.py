from __future__ import annotations

from pathlib import Path

from loguru import logger

from .config import APIConfig


def setup_logging(app_name: str = "meteosuisse", logs_dir: Path | None = None) -> None:
    if logs_dir is None:
        # Default to canonical artifacts/logs directory
        cfg = APIConfig()
        logs_dir = cfg.artifacts_logs_dir

    logger.remove()
    # File: DEBUG, rotation 1 MB
    logger.add(
        logs_dir / f"{app_name}.log",
        level="DEBUG",
        rotation="1 MB",
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <7} | "
            "{process.name}:{thread.name} | {name}:{function}:{line} - {message}"
        ),
    )
    # Intentionally no console sink; use rich for CLI output.
