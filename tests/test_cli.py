import argparse

import pytest

from loadtest.cli import (
    build_parser,
    load_json_body,
    parse_header,
    threshold_failures,
)


def test_parse_header_splits_only_first_colon() -> None:
    assert parse_header("Authorization: Bearer value:part") == (
        "Authorization",
        "Bearer value:part",
    )


def test_parse_header_rejects_invalid_value() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_header("missing-separator")


def test_load_json_body_reads_inline_json() -> None:
    assert load_json_body('{"name": "Maria"}', None) == {"name": "Maria"}


def test_parser_accepts_quality_thresholds() -> None:
    args = build_parser().parse_args(
        [
            "--url",
            "http://localhost",
            "--max-error-rate",
            "1.5",
            "--max-p95-ms",
            "250",
        ]
    )

    assert args.max_error_rate == 1.5
    assert args.max_p95_ms == 250.0


def test_parser_rejects_invalid_error_rate_threshold() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--url", "http://localhost", "--max-error-rate", "101"])


def test_threshold_failures_reports_each_exceeded_limit() -> None:
    report = {
        "error_rate_pct": 2.5,
        "latency_ms": {"p95": 320.0},
    }

    failures = threshold_failures(
        report,
        max_error_rate=1.0,
        max_p95_ms=250.0,
    )

    assert failures == [
        "error rate 2.500% exceeds 1.000%",
        "p95 latency 320.000 ms exceeds 250.000 ms",
    ]


def test_threshold_failures_allows_values_at_limits() -> None:
    report = {
        "error_rate_pct": 1.0,
        "latency_ms": {"p95": 250.0},
    }

    assert not threshold_failures(
        report,
        max_error_rate=1.0,
        max_p95_ms=250.0,
    )
