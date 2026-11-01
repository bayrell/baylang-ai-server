"""Регистрация всех API-маршрутов."""

from fastapi import FastAPI

from core.auth import router as auth_router
from core.routes import agents, chats, models, providers, system


def register_all_routes(app: FastAPI) -> None:
    """Подключить все маршруты к приложению."""
    app.include_router(system.router)
    app.include_router(auth_router)
    app.include_router(chats.router)
    app.include_router(providers.router)
    app.include_router(models.router)
    app.include_router(agents.router)


__all__ = ["register_all_routes"]
