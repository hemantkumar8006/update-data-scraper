# syntax=docker/dockerfile:1

# ---- Base builder image ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg2 and lxml
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       curl \
       ca-certificates \
       libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Install deps to a local folder to copy later
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip freeze > /tmp/requirements.lock.txt

# ---- Final runtime image ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy only necessary files
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app

# Drop privileges
USER appuser

EXPOSE 8000

# Healthcheck (basic HTTP)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://localhost:8000/status || exit 1

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-k", "gthread", "-b", "0.0.0.0:8000", "main:create_app()"]



