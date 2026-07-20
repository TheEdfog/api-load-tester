from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from math import ceil
from typing import Any

from loadtest.models import LoadConfig, Observation


def percentile(values: list[float], percentile_value: float) -> float:
    """Calculate a nearest-rank percentile for a non-empty list."""
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0 <= percentile_value <= 100:
        raise ValueError("percentile_value must be between 0 and 100")
    ordered = sorted(values)
    rank = max(1, ceil(percentile_value / 100 * len(ordered)))
    return ordered[rank - 1]


def build_report(
    config: LoadConfig,
    observations: list[Observation],
    wall_duration: float,
) -> dict[str, Any]:
    latencies_ms = [item.latency_seconds * 1000 for item in observations]
    status_counts = Counter(str(item.status) for item in observations if item.status is not None)
    transport_errors = Counter(item.error for item in observations if item.error is not None)
    successful = sum(item.successful for item in observations)
    completed = len(observations)
    unsuccessful = completed - successful

    latency_summary = {
        "min": round(min(latencies_ms), 3),
        "average": round(sum(latencies_ms) / completed, 3),
        "p50": round(percentile(latencies_ms, 50), 3),
        "p95": round(percentile(latencies_ms, 95), 3),
        "p99": round(percentile(latencies_ms, 99), 3),
        "max": round(max(latencies_ms), 3),
    }

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "target": {
            "url": config.url,
            "method": config.method,
            "start_rate_rps": config.start_rate,
            "end_rate_rps": config.final_rate,
            "scheduling_duration_seconds": config.duration,
            "concurrency": config.concurrency,
            "timeout_seconds": config.timeout,
        },
        "attempted_requests": completed,
        "completed_requests": completed,
        "successful_requests": successful,
        "unsuccessful_requests": unsuccessful,
        "error_rate_pct": round(unsuccessful / completed * 100, 3),
        "wall_duration_seconds": round(wall_duration, 3),
        "achieved_rps": round(completed / wall_duration, 3),
        "latency_ms": latency_summary,
        "status_codes": dict(sorted(status_counts.items())),
        "transport_errors": dict(sorted(transport_errors.items())),
    }
