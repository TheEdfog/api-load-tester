# API Load Tester

I built this tool while investigating the performance of ML APIs. It sends HTTP requests at a constant or gradually increasing rate and writes a JSON report with throughput, errors, status codes and p50/p95/p99 latency.

The repository includes a small FastAPI service for local experiments. It is intentionally a single-machine tool, not a replacement for distributed load-testing systems such as k6, Gatling or Locust.

## How it works

```text
CLI -> request scheduler -> bounded asyncio workers -> target API -> JSON report
```

The scheduler controls the requested rate while a semaphore limits requests in flight. Response bodies are consumed but not stored, so reports do not retain API data and memory use stays predictable.

## Run with Docker

Start the demo API:

```bash
docker compose up --build -d demo-api
```

Run a ten-second test at 100 requests per second:

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

Stop the environment with `docker compose down`.

## Run locally

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
python -m pip install -e ".[dev,demo]"
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

`--end-rate` is optional; without it the load stays constant. Headers can be repeated with `--header`, and the request body can come from `--body` or `--body-file`.

## Example result

```json
{
  "attempted_requests": 500,
  "successful_requests": 500,
  "error_rate_pct": 0.0,
  "achieved_rps": 98.71,
  "latency_ms": {"p50": 7.12, "p95": 14.81, "p99": 21.34},
  "status_codes": {"200": 500}
}
```

## Checks

```bash
pytest
ruff check .
ruff format --check .
```

## Limits

- Requested and achieved throughput can differ when the client or server reaches the concurrency limit.
- Latencies are kept in memory, so very long runs would benefit from a streaming histogram.
- Results against the bundled demo service say nothing about production capacity.
