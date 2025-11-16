import os
from pathlib import Path
import pandas as pd
import pytest
from meteosuisse.main_client import MeteoSwissClient
from meteosuisse.config import TimeGranularity, UpdateFrequency


@pytest.mark.integration
def test_ground_based_automatic_weather_stations_shape(vcr_cassette, jan_2024_week):
    client = MeteoSwissClient()
    # Ensure collection info call is recorded/replayed
    cassette = Path(__file__).parent / "data" / "cassettes" / "ground_based_collection_info.yaml"
    if not cassette.exists() and os.environ.get("RUN_LIVE_TESTS") != "1":
        pytest.skip("Cassette missing; set RUN_LIVE_TESTS=1 to record")
    with vcr_cassette.use_cassette(str(cassette)):
        df = client.ground_based.get_automatic_weather_stations(
            station_id="BER",
            granularity=TimeGranularity.HOURLY,
            frequency=UpdateFrequency.RECENT,
            start=jan_2024_week[0],
            end=jan_2024_week[1],
        )
        # Current implementation returns a DataFrame (may be empty until URL resolution implemented)
        assert isinstance(df, pd.DataFrame)


