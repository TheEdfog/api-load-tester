# Нагрузочное тестирование API

Этот инструмент появился во время исследования производительности ML API. Он отправляет HTTP-запросы с постоянной или линейно растущей интенсивностью и сохраняет JSON-отчёт: throughput, ошибки, HTTP-статусы и задержки p50/p95/p99.

В репозитории есть небольшой FastAPI-сервис для локальных экспериментов. Инструмент рассчитан на запуск с одной машины и не пытается заменить распределённые системы вроде k6, Gatling или Locust.

## Как устроен запуск

![Схема нагрузочного тестирования](docs/architecture.svg)

Планировщик задаёт целевой RPS, а число одновременно выполняемых задач ограничивается параметром `concurrency`. Если сервис не успевает обрабатывать запросы, планирование ждёт свободного слота: фактический RPS снижается, но очередь не растёт бесконтрольно. Тела ответов считываются, но не сохраняются.

## Запуск через Docker

Поднять демонстрационный API:

```bash
docker compose up --build -d demo-api
```

Выполнить десятисекундный тест с интенсивностью 100 запросов в секунду:

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

Остановить окружение: `docker compose down`.

## Локальный запуск

Требуется Python 3.11+.

```bash
python -m venv .venv
python -m pip install -e ".[dev,demo]"
uvicorn demo_api.main:app --host 0.0.0.0 --port 8000
```

В другом терминале:

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

Параметр `--end-rate` необязателен: без него нагрузка остаётся постоянной. Заголовки можно передавать повторяющимся `--header`, а JSON-тело через `--body` или `--body-file`.

## Пример результата

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

## Проверки

```bash
pytest
ruff check .
ruff format --check .
```

## Ограничения

- Целевой и фактический throughput расходятся, если клиент или сервер достигает лимита concurrency.
- Значения latency хранятся в памяти; для очень долгих тестов лучше использовать потоковую гистограмму.
- Результаты на встроенном demo API ничего не говорят о производительности production-сервиса.
