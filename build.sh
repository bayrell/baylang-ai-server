#!/usr/bin/env bash
#
# build.sh — сборка и запуск BayLang AI.
#
# Команды:
#   ./build.sh frontend        — установить зависимости и собрать Vue-приложение
#   ./build.sh docker          — собрать Docker-образ
#   ./build.sh docker-run      — собрать и запустить контейнер
#   ./build.sh docker-push     — отправить образ в реестр
#   ./build.sh docker-stop     — остановить и удалить контейнер
#   ./build.sh docker-logs     — логи контейнера
#   ./build.sh backend         — установить Python-зависимости
#   ./build.sh cloudflare      — собрать фронтенд и задеплоить в Cloudflare Workers
#   ./build.sh dev             — локальный запуск backend + frontend
#   ./build.sh clean           — удалить артефакты сборки
#   ./build.sh all             — frontend + docker
#
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-baylang-ai}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="${CONTAINER_NAME:-baylang-ai}"
HOST_PORT="${HOST_PORT:-8000}"
DATA_DIR="${DATA_DIR:-./data}"
DOCKER_BIN="${DOCKER:-docker}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

# -----------------------------------------------------------------------------
# Функции
# -----------------------------------------------------------------------------
usage()
{
    sed -n '3,20p' "$0" | sed 's/^# \{0,1\}//'
}

build_frontend()
{
    echo "==> Сборка frontend (Vue 3 + Vite)"
    if command -v npm >/dev/null 2>&1; then
        npm install --no-audit --no-fund
        npm run build
    else
        echo "Ошибка: npm не найден. Установите Node.js 20+." >&2
        return 1
    fi
    echo "==> Frontend собран: src/dist"
}

build_backend()
{
    echo "==> Установка Python-зависимостей"
    if command -v uv >/dev/null 2>&1; then
        uv pip install --system -r src/requirements.txt
    else
        python3 -m pip install -r src/requirements.txt
    fi
}

build_docker()
{
    echo "==> Сборка Docker-образа ${IMAGE_NAME}:${IMAGE_TAG}"
    "${DOCKER_BIN}" build \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_NAME}:latest" \
        .
    echo "==> Образ готов: ${IMAGE_NAME}:${IMAGE_TAG}"
}

run_docker()
{
    echo "==> Запуск контейнера ${CONTAINER_NAME}"
    mkdir -p "${DATA_DIR}"
    "${DOCKER_BIN}" rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    "${DOCKER_BIN}" run -d \
        --name "${CONTAINER_NAME}" \
        -p "${HOST_PORT}:8000" \
        -v "$(pwd)/${DATA_DIR}:/app/data" \
        -e "JWT_SECRET=${JWT_SECRET:-change-me-in-production}" \
        "${IMAGE_NAME}:${IMAGE_TAG}"
    echo "==> Контейнер запущен: http://localhost:${HOST_PORT}"
}

push_docker()
{
    echo "==> Отправка образа ${IMAGE_NAME}:${IMAGE_TAG} в реестр"
    "${DOCKER_BIN}" push "${IMAGE_NAME}:${IMAGE_TAG}"
}

stop_docker()
{
    echo "==> Остановка контейнера ${CONTAINER_NAME}"
    "${DOCKER_BIN}" stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    "${DOCKER_BIN}" rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}

docker_logs()
{
    "${DOCKER_BIN}" logs -f "${CONTAINER_NAME}"
}

deploy_cloudflare()
{
    echo "==> Сборка frontend и деплой в Cloudflare Workers"
    build_frontend
    if command -v npx >/dev/null 2>&1; then
        npx wrangler deploy
    else
        echo "Ошибка: npx не найден. Установите Node.js 20+." >&2
        return 1
    fi
}

run_dev()
{
    echo "==> Локальный запуск: backend на :8000, frontend на :5173"
    build_backend
    (
        cd src
        uvicorn app:create_app --factory --reload --host 0.0.0.0 --port 8000
    ) &
    BACKEND_PID=$!
    trap 'kill ${BACKEND_PID} 2>/dev/null || true' EXIT

    npm install --no-audit --no-fund
    npm run dev
}

clean()
{
    echo "==> Очистка артефактов"
    rm -rf src/dist
    find src -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
    rm -rf "${DATA_DIR}"
}

# -----------------------------------------------------------------------------
# Диспетчер команд
# -----------------------------------------------------------------------------
case "${1:-help}" in
    frontend|build-frontend)
        build_frontend
        ;;

    backend|install-backend)
        build_backend
        ;;

    docker|docker-build)
        build_docker
        ;;

    docker-run|run)
        build_docker
        run_docker
        ;;

    docker-push|push)
        push_docker
        ;;

    docker-stop|stop)
        stop_docker
        ;;

    docker-logs|logs)
        docker_logs
        ;;

    cloudflare|workers|deploy)
        deploy_cloudflare
        ;;

    dev)
        run_dev
        ;;

    test)
        echo "==> Тесты"
        python3 -m pytest -q
        ;;

    clean)
        clean
        ;;

    all)
        build_frontend
        build_docker
        ;;

    help|-h|--help)
        usage
        ;;

    *)
        echo "Неизвестная команда: ${1}" >&2
        usage
        exit 1
        ;;
esac
