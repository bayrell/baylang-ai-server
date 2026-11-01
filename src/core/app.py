"""Сборка FastAPI-приложения: репозитории, сервисы, маршруты и статика."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.app_meta import APP_DESCRIPTION, APP_TITLE
from core.config import Env
from core.container import container
from core.database.d1 import D1Database
from core.database.sqlite import DEFAULT_DATABASE_PATH, SqliteDatabase
from core.repositories.agent_repository import AgentRepository
from core.repositories.chat_repository import ChatRepository
from core.repositories.message_repository import MessageRepository
from core.repositories.model_repository import ModelRepository
from core.repositories.provider_repository import ProviderRepository
from core.repositories.user_repository import UserRepository
from core.routes import register_all_routes
from core.services.agent_factory import AgentFactory
from core.services.chat_service import ChatService

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(SRC_DIR, "dist")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")


# ----------------------------------------------------------------------
# Регистрация зависимостей
# ----------------------------------------------------------------------
def register_repositories() -> None:
    """Зарегистрировать Record-репозитории."""
    container.singleton(
        "user_repository",
        lambda c: UserRepository(c.get("database")),
    )
    container.singleton(
        "provider_repository",
        lambda c: ProviderRepository(c.get("database")),
    )
    container.singleton(
        "model_repository",
        lambda c: ModelRepository(c.get("database")),
    )
    container.singleton(
        "agent_repository",
        lambda c: AgentRepository(c.get("database")),
    )
    container.singleton(
        "chat_repository",
        lambda c: ChatRepository(c.get("database")),
    )
    container.singleton(
        "message_repository",
        lambda c: MessageRepository(c.get("database")),
    )


def register_services() -> None:
    """Зарегистрировать сервисы приложения."""
    container.singleton(
        "agent_factory",
        lambda c: AgentFactory(
            c.get("agent_repository"),
            c.get("model_repository"),
            c.get("provider_repository"),
        ),
    )
    container.singleton(
        "chat_service",
        lambda c: ChatService(
            c.get("chat_repository"),
            c.get("message_repository"),
            c.get("agent_factory"),
        ),
    )


def register_routes(app: FastAPI) -> None:
    """Подключить API-маршруты."""
    register_all_routes(app)


def register_static(app: FastAPI) -> None:
    """Отдать собранный фронтенд (SPA) и статические файлы."""
    if os.path.isdir(ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")

        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)

        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Сборка фронтенда не найдена. Выполните `npm run build` или используйте Docker-образ.",
        )


def create_cors(app: FastAPI) -> None:
    """Разрешить CORS (нужно для dev-режима Vite на отдельном порту)."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ----------------------------------------------------------------------
# Точки входа
# ----------------------------------------------------------------------
def create_app() -> FastAPI:
    """Приложение для Docker (SQLite + статика фронтенда)."""
    container.singleton("env", lambda c: Env(os.environ))
    container.singleton(
        "database",
        lambda c: SqliteDatabase(c.get("env").get("DATABASE_PATH", DEFAULT_DATABASE_PATH)),
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database = container.get("database")
        await database.initialize()
        yield
        close = getattr(database, "close", None)
        if callable(close):
            close()

    container.singleton(
        "app",
        lambda: FastAPI(title=APP_TITLE, description=APP_DESCRIPTION, lifespan=lifespan),
    )

    app = container.get("app")
    create_cors(app)
    register_repositories()
    register_services()
    register_routes(app)
    register_static(app)
    return app


def create_cloudflare_app(env: Any) -> FastAPI:
    """Приложение для Cloudflare Workers (D1 + без статики)."""
    container.singleton("env", lambda c: Env(env))
    container.singleton("database", lambda c: D1Database(c.get("env")))

    container.singleton(
        "app",
        lambda: FastAPI(title=APP_TITLE, description=APP_DESCRIPTION),
    )

    app = container.get("app")
    create_cors(app)
    register_repositories()
    register_services()
    register_routes(app)
    return app


__all__ = [
    "APP_TITLE",
    "create_app",
    "create_cloudflare_app",
    "register_repositories",
    "register_services",
    "register_routes",
    "register_static",
]
