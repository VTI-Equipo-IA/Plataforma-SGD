# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5001

WORKDIR /app

# System libs:
# - libgomp1: required by some scientific wheels (e.g., faiss-cpu) for OpenMP
# - libpq5: PostgreSQL client library (safe default for psycopg2/psycopg)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN useradd -m -u 10001 appuser

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 5001

CMD ["python", "app.py"]
