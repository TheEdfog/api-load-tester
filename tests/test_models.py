import pytest

from loadtest.models import LoadConfig


def test_constant_rate_uses_start_rate_as_final_rate() -> None:
    config = LoadConfig(url="http://localhost", start_rate=25)
    assert config.final_rate == 25


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("start_rate", 0),
        ("end_rate", 0),
        ("duration", 0),
        ("concurrency", 0),
        ("timeout", 0),
    ],
)
def test_invalid_positive_values_are_rejected(field: str, value: int) -> None:
    arguments = {"url": "http://localhost", field: value}
    with pytest.raises(ValueError):
        LoadConfig(**arguments)


def test_url_must_be_http() -> None:
    with pytest.raises(ValueError):
        LoadConfig(url="localhost:8000")
