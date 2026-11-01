"""Маршруты настроек моделей."""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import (
    get_current_user,
    get_model_repository,
    get_provider_repository,
)
from core.schemas.model import ModelCreate

router = APIRouter(prefix="/api/models", tags=["models"])


def serialize_model(row: Dict[str, Any]) -> Dict[str, Any]:
    """Преобразовать строку БД в ответ API."""
    extra: Dict[str, Any] = {}
    if row.get("extra"):
        try:
            loaded = json.loads(row["extra"])
            extra = loaded if isinstance(loaded, dict) else {}
        except (TypeError, ValueError):
            extra = {}

    return {
        "id": row.get("id"),
        "provider_id": row.get("provider_id"),
        "provider_name": row.get("provider_name"),
        "name": row.get("name"),
        "temperature": row.get("temperature"),
        "max_tokens": row.get("max_tokens"),
        "extra": extra,
        "created_at": row.get("created_at"),
    }


@router.get("")
async def list_models(
    user=Depends(get_current_user),
    model_repo=Depends(get_model_repository),
):
    """Список моделей пользователя."""
    rows = await model_repo.find_by_user(user["id"])
    return [serialize_model(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_model(
    data: ModelCreate,
    user=Depends(get_current_user),
    model_repo=Depends(get_model_repository),
    provider_repo=Depends(get_provider_repository),
):
    """Создать модель."""
    provider = await provider_repo.find_by_id(data.provider_id)
    if not provider or provider.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Провайдер не найден")

    extra = json.dumps(data.extra or {}, ensure_ascii=False)
    model_id = await model_repo.create(
        user_id=user["id"],
        provider_id=data.provider_id,
        name=data.name.strip(),
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        extra=extra,
    )

    row = await model_repo.find_by_id(model_id)
    return serialize_model(row) if row else {"id": model_id}


@router.put("/{model_id}")
async def update_model(
    model_id: int,
    data: ModelCreate,
    user=Depends(get_current_user),
    model_repo=Depends(get_model_repository),
    provider_repo=Depends(get_provider_repository),
):
    """Редактировать модель."""
    row = await model_repo.find_by_id(model_id)
    if not row or row.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Модель не найдена")

    provider = await provider_repo.find_by_id(data.provider_id)
    if not provider or provider.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Провайдер не найден")

    await model_repo.update(
        model_id=model_id,
        user_id=user["id"],
        provider_id=data.provider_id,
        name=data.name.strip(),
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        extra=json.dumps(data.extra or {}, ensure_ascii=False),
    )

    updated = await model_repo.find_by_id(model_id)
    return serialize_model(updated) if updated else {"id": model_id}


@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    user=Depends(get_current_user),
    model_repo=Depends(get_model_repository),
):
    """Удалить модель."""
    row = await model_repo.find_by_id(model_id)
    if not row or row.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Модель не найдена")

    await model_repo.delete(model_id, user["id"])
    return {"ok": True}


__all__ = ["router", "serialize_model"]
