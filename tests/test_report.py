from loadtest.models import LoadConfig, Observation
from loadtest.report import build_report, percentile


def test_nearest_rank_percentile() -> None:
    values = [1, 2, 3, 4, 5]
    assert percentile(values, 50) == 3
    assert percentile(values, 95) == 5


def test_report_aggregates_statuses_errors_and_latency() -> None:
    config = LoadConfig(url="http://localhost", start_rate=3, duration=1)
    observations = [
        Observation(0.010, 200),
        Observation(0.020, 503),
        Observation(0.030, None, "timeout"),
    ]

    report = build_report(config, observations, wall_duration=1.5)

    assert report["completed_requests"] == 3
    assert report["successful_requests"] == 1
    assert report["error_rate_pct"] == 66.667
    assert report["achieved_rps"] == 2.0
    assert report["latency_ms"]["p50"] == 20.0
    assert report["status_codes"] == {"200": 1, "503": 1}
    assert report["transport_errors"] == {"timeout": 1}
