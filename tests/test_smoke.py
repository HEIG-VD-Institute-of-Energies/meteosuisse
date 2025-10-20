from meteosuisse import MeteoSwissClient


def test_client_instantiation():
    client = MeteoSwissClient()
    assert client is not None
