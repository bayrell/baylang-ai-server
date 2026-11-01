# syntax=docker/dockerfile:1.7

###############################################################################
# Stage 1 — Frontend (Vue 3 + Vite)
# Собираем SPA в dist, который затем отдаёт FastAPI.
# Исходники фронтенда лежат плоско в src/, поэтому корень Vite — сам src/.
###############################################################################
FROM node:22-alpine AS frontend

WORKDIR /build

COPY src/package.json ./
RUN npm install --no-audit --no-fund

COPY src/index.html src/vite.config.js ./
COPY src/main.js ./
COPY src/pages ./pages
COPY src/services ./services
COPY src/assets ./assets

RUN npm run build


###############################################################################
# Stage 2 — Backend (FastAPI + pydantic-ai)
###############################################################################
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src \
    DATABASE_PATH=/app/data/baylang.sqlite3 \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Зависимости отдельным слоем — переиспользуются при изменении кода.
COPY src/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Код приложения и собранный фронтенд.
COPY src /app/src
COPY --from=frontend /build/dist /app/src/dist

RUN mkdir -p /app/data \
    && useradd --create-home --uid 10001 baylang \
    && chown -R baylang:baylang /app

USER baylang

VOLUME ["/app/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
