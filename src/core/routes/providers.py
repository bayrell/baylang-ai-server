"""Маршруты настроек провайдеров."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import get_current_user, get_provider_repository
from core.schemas.provider import ProviderCreate
from core.services.provider_service import dump_extra, serialize_provider

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("")
async def list_providers(
    user=Depends(get_current_user),
    provider_repo=Depends(get_provider_repository),
):
    """Список провайдеров пользователя."""
    rows = await provider_repo.find_by_user(user["id"])
    return [serialize_provider(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderCreate,
    user=Depends(get_current_user),
    provider_repo=Depends(get_provider_repository),
):
    """Создать провайдера."""
    extra = dump_extra(data.only, data.extra)
    provider_id = await provider_repo.create(
        user_id=user["id"],
        name=data.name.strip(),
        url=data.url.strip(),
        api_key=data.api_key.strip(),
        extra=extra,
        is_default=data.is_default,
    )

    row = await provider_repo.find_by_id(provider_id)
    return serialize_provider(row) if row else {"id": provider_id}


@router.put("/{provider_id}")
async def update_provider(
    provider_id: int,
    data: ProviderCreate,
    user=Depends(get_current_user),
    provider_repo=Depends(get_provider_repository),
):
    """Редактировать провайдера."""
    row = await provider_repo.find_by_id(provider_id)
    if not row or row.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Провайдер не найден")

    api_key = data.api_key.strip()
    if not api_key or api_key.startswith("*"):
        # Не показываем маску обратно — сохраняем прежний ключ.
        api_key = row.get("api_key") or ""

    await provider_repo.update(
        provider_id=provider_id,
        user_id=user["id"],
        name=data.name.strip(),
        url=data.url.strip(),
        api_key=api_key,
        extra=dump_extra(data.only, data.extra),
        is_default=data.is_default,
    )

    updated = await provider_repo.find_by_id(provider_id)
    return serialize_provider(updated) if updated else {"id": provider_id}


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: int,
    user=Depends(get_current_user),
    provider_repo=Depends(get_provider_repository),
):
    """Удалить провайдера."""
    row = await provider_repo.find_by_id(provider_id)
    if not row or row.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Провайдер не найден")

    await provider_repo.delete(provider_id, user["id"])
    return {"ok": True}


__all__ = ["router"]
