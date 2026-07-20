FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY loadtest ./loadtest
COPY demo_api ./demo_api
RUN pip install --no-cache-dir ".[demo]"

ENTRYPOINT ["api-load-test"]

