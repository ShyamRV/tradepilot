# TradePilot production image — API (uvicorn) default; override CMD for worker.
#   docker run ... tradepilot-api
#   docker run ... tradepilot-api python -m apps.worker.main
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/packages \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin tradepilot

COPY pyproject.toml README.md ./
COPY packages ./packages
COPY apps ./apps
COPY migrations ./migrations
COPY schemas ./schemas
COPY scripts ./scripts

RUN pip install --no-cache-dir -e ".[prod]" \
    && mkdir -p /app/data \
    && chown -R tradepilot:tradepilot /app

USER tradepilot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# Default: FastAPI via uvicorn. Worker entry:
#   command: ["python", "-m", "apps.worker.main"]
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
