# API Load Tester

A small asynchronous HTTP load-testing tool built with Python and `aiohttp`. It generates constant or linearly increasing request rates and produces a compact JSON report with throughput, status-code distribution, error rate, and latency percentiles.

The repository also contains a FastAPI demo service, automated tests, Docker Compose, and CI. It is designed as an understandable engineering case study rather than a replacement for k6, Gatling, or Locust.

## What it demonstrates

- asynchronous HTTP requests with bounded concurrency;
- constant and ramp-up traffic profiles;
- p50, p95, and p99 latency calculation;
- achieved throughput and error-rate reporting;
- separation between traffic generation, aggregation, and CLI concerns;
- reproducible local execution and automated quality checks.

## Architecture

```text
CLI arguments / JSON body
          │
          ▼
   request scheduler ── target requests per second
          │
          ▼
 asyncio task pool ──── concurrency semaphore
          │
          ▼
     aiohttp client ─── target HTTP API
          │
          ▼
 compact observations ─ status + latency + error category
          │
          ▼
      JSON summary ──── RPS, errors, p50/p95/p99
```

Response bodies are consumed but not retained. This keeps memory usage predictable and avoids writing potentially sensitive API responses to reports.

## Quick start with Docker

Start the demo API:

```bash
docker compose up --build -d demo-api
```

Run a 10-second test at 100 requests per second:

```bash
docker compose run --rm load-tester \
  --url http://demo-api:8000/names \
  --method POST \
  --start-rate 100 \
  --duration 10 \
  --concurrency 200 \
  --body-file examples/name.json \
  --output reports/demo.json
```

Stop the environment:

```bash
docker compose down
```

## Local installation

Python 3.11+ is recommended.

```bash
python -m venv .venv
.venv/Scripts/activate
python -m pip install -e ".[dev,demo]"
```

On Linux or macOS, activate the environment with `source .venv/bin/activate`.

Start the demo API:

```bash
uvicorn demo_api.main:app --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
api-load-test \
  --url http://localhost:8000/names \
  --method POST \
  --start-rate 50 \
  --end-rate 500 \
  --duration 30 \
  --concurrency 250 \
  --body-file examples/name.json \
  --output reports/ramp.json
```

You can also run the package directly:

```bash
python -m loadtest --url http://localhost:8000/health --start-rate 20 --duration 5
```

## CLI options

| Option | Description |
|---|---|
| `--url` | Target URL; required |
| `--method` | HTTP method; default `GET` |
| `--start-rate` | Initial target requests per second |
| `--end-rate` | Final target rate; omit for constant load |
| `--duration` | Scheduling duration in seconds |
| `--concurrency` | Maximum in-flight requests |
| `--timeout` | Per-request timeout in seconds |
| `--header` | Repeatable `Name: value` header |
| `--body` | Inline JSON request body |
| `--body-file` | Path to a JSON request body |
| `--output` | JSON report path |

`--body` and `--body-file` are mutually exclusive. A non-2xx/3xx response is counted as an unsuccessful response but is still represented by its HTTP status code. Transport failures and timeouts are reported separately.

## Example report

```json
{
  "attempted_requests": 500,
  "completed_requests": 500,
  "successful_requests": 500,
  "error_rate_pct": 0.0,
  "achieved_rps": 98.71,
  "latency_ms": {
    "p50": 7.12,
    "p95": 14.81,
    "p99": 21.34
  },
  "status_codes": {
    "200": 500
  }
}
```

The full schema also includes the requested traffic profile, wall-clock duration, minimum/average/maximum latency, and transport error categories.

## Development

```bash
pytest
ruff check .
ruff format --check .
```

CI runs the same checks for every push and pull request.

## Design limitations

- The scheduler runs on a single machine and does not coordinate distributed workers.
- Actual throughput can fall below the requested rate when the target or client reaches the configured concurrency limit.
- Percentiles are calculated from in-memory latency observations; very long tests should use streaming histograms.
- Results from a local demo API are not representative of production capacity.

## Background

This project is a cleaned-up, reproducible version of a load-testing approach originally used to investigate ML API performance. Production systems, data, endpoints, and results are not included.
