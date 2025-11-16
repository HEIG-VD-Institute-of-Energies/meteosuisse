import datetime as dt
import os
import sys
from pathlib import Path

import pytest
import vcr

CASSETTE_DIR = Path(__file__).parent / "data" / "cassettes"

vcr_recorder = vcr.VCR(
    cassette_library_dir=str(CASSETTE_DIR),
    record_mode="once",
    filter_headers=["authorization"],
    decode_compressed_response=True,
)


@pytest.fixture(scope="session")
def vcr_cassette():
    return vcr_recorder


@pytest.fixture
def jan_2024_week():
    return dt.datetime(2024, 1, 1), dt.datetime(2024, 1, 7, 23, 59, 59)


def pytest_collection_modifyitems(config, items):
    # Auto-skip live tests unless explicitly enabled
    run_live = os.environ.get("RUN_LIVE_TESTS") == "1"
    for item in items:
        if "live" in item.keywords and not run_live:
            item.add_marker(pytest.mark.skip(reason="RUN_LIVE_TESTS=1 required"))


# Ensure src/ is importable without installation
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
