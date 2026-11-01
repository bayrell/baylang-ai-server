"""Системные маршруты: health-check и общая информация о приложении."""

from __future__ import annotations

from fastapi import APIRouter

from core.app_meta import APP_TITLE, APP_VERSION

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
async def health():
    """Проверка готовности сервиса (используется в HEALTHCHECK)."""
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}


@router.get("/info")
async def info():
    """Название и версия приложения."""
    return {"app": APP_TITLE, "version": APP_VERSION}


__all__ = ["router"]
