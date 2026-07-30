from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from loadtest.models import LoadConfig
from loadtest.report import build_report
from loadtest.runner import run_load_test


def percentage(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 100:
        raise argparse.ArgumentTypeError("percentage must be between 0 and 100")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def parse_header(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("headers must use the form 'Name: value'")
    name, header_value = value.split(":", 1)
    if not name.strip():
        raise argparse.ArgumentTypeError("header name cannot be empty")
    return name.strip(), header_value.strip()


def load_json_body(inline: str | None, file_path: Path | None) -> Any | None:
    if inline is not None:
        return json.loads(inline)
    if file_path is not None:
        with file_path.open(encoding="utf-8") as body_file:
            return json.load(body_file)
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run asynchronous HTTP load tests")
    parser.add_argument("--url", required=True, help="Target HTTP or HTTPS URL")
    parser.add_argument(
        "--method", default="GET", choices=["GET", "POST", "PUT", "PATCH", "DELETE"]
    )
    parser.add_argument(
        "--start-rate", type=float, default=10.0, help="Initial target requests per second"
    )
    parser.add_argument("--end-rate", type=float, help="Final target RPS for a linear ramp")
    parser.add_argument("--duration", type=int, default=10, help="Scheduling duration in seconds")
    parser.add_argument("--concurrency", type=int, default=100, help="Maximum in-flight requests")
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="Per-request timeout in seconds"
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        type=parse_header,
        help="Repeatable 'Name: value' header",
    )
    body_group = parser.add_mutually_exclusive_group()
    body_group.add_argument("--body", help="Inline JSON request body")
    body_group.add_argument("--body-file", type=Path, help="Path to a JSON request body")
    parser.add_argument(
        "--output", type=Path, default=Path("reports/result.json"), help="JSON report path"
    )
    parser.add_argument(
        "--max-error-rate",
        type=percentage,
        help="Exit with an error when unsuccessful requests exceed this percentage",
    )
    parser.add_argument(
        "--max-p95-ms",
        type=positive_float,
        help="Exit with an error when p95 latency exceeds this value in milliseconds",
    )
    return parser


def threshold_failures(
    report: dict[str, Any],
    *,
    max_error_rate: float | None,
    max_p95_ms: float | None,
) -> list[str]:
    failures: list[str] = []
    error_rate = float(report["error_rate_pct"])
    p95_ms = float(report["latency_ms"]["p95"])

    if max_error_rate is not None and error_rate > max_error_rate:
        failures.append(f"error rate {error_rate:.3f}% exceeds {max_error_rate:.3f}%")
    if max_p95_ms is not None and p95_ms > max_p95_ms:
        failures.append(f"p95 latency {p95_ms:.3f} ms exceeds {max_p95_ms:.3f} ms")
    return failures


def main() -> None:
    args = build_parser().parse_args()
    try:
        body = load_json_body(args.body, args.body_file)
        config = LoadConfig(
            url=args.url,
            method=args.method,
            start_rate=args.start_rate,
            end_rate=args.end_rate,
            duration=args.duration,
            concurrency=args.concurrency,
            timeout=args.timeout,
            headers=dict(args.header),
            json_body=body,
        )
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"configuration error: {exc}") from exc

    observations, wall_duration = asyncio.run(run_load_test(config))
    report = build_report(config, observations, wall_duration)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

    failures = threshold_failures(
        report,
        max_error_rate=args.max_error_rate,
        max_p95_ms=args.max_p95_ms,
    )
    if failures:
        raise SystemExit("thresholds failed: " + "; ".join(failures))
