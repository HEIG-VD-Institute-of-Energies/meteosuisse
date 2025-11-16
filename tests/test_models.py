from dataclasses import is_dataclass

from meteosuisse.models import CollectionMetadata, DataInventory, Parameter, Station


def test_dataclass_shapes():
    assert is_dataclass(Station)
    assert is_dataclass(Parameter)
    assert is_dataclass(DataInventory)
    assert is_dataclass(CollectionMetadata)


def test_station_defaults():
    s = Station(identifier="BER", name="Bern")
    assert s.identifier == "BER"
    assert s.canton is None


def test_parameter_defaults():
    p = Parameter(identifier="precip", description="Precip", time_interval="h")
    assert p.decimal_places is None
    assert p.unit is None
