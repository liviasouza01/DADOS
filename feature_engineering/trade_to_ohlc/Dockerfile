FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONPATH=/app \
    POETRY_VERSION=2.4.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    KAFKA_BROKER_ADDRESS=redpanda:9092

WORKDIR /app

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --only main

COPY . .

CMD ["python", "main.py"]
