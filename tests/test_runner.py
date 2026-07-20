from loadtest.models import LoadConfig
from loadtest.runner import rate_for_second


def test_constant_rate() -> None:
    config = LoadConfig(url="http://localhost", start_rate=50, duration=3)
    assert [rate_for_second(config, second) for second in range(3)] == [50, 50, 50]


def test_linear_ramp_reaches_both_endpoints() -> None:
    config = LoadConfig(url="http://localhost", start_rate=10, end_rate=30, duration=3)
    assert [rate_for_second(config, second) for second in range(3)] == [10, 20, 30]
