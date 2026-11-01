"""Маршруты настроек агентов (персон)."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from core.dependencies import (
    get_agent_repository,
    get_current_user,
    get_model_repository,
)
from core.schemas.agent import AgentCreate

router = APIRouter(prefix="/api/agents", tags=["agents"])


def serialize_agent(row: Dict[str, Any]) -> Dict[str, Any]:
    """Преобразовать строку БД в ответ API."""
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "system_prompt": row.get("system_prompt") or "",
        "model_id": row.get("model_id"),
        "model_name": row.get("model_name"),
        "created_at": row.get("created_at"),
    }


@router.get("")
async def list_agents(
    user=Depends(get_current_user),
    agent_repo=Depends(get_agent_repository),
):
    """Список агентов пользователя."""
    rows = await agent_repo.find_by_user(user["id"])
    return [serialize_agent(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    user=Depends(get_current_user),
    agent_repo=Depends(get_agent_repository),
    model_repo=Depends(get_model_repository),
):
    """Создать агента."""
    if data.model_id:
        model = await model_repo.find_by_id(data.model_id)
        if not model or model.get("user_id") != user["id"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Модель не найдена")

    agent_id = await agent_repo.create(
        user_id=user["id"],
        name=data.name.strip(),
        system_prompt=data.system_prompt or "",
        model_id=data.model_id,
    )

    row = await agent_repo.find_by_id(agent_id)
    return serialize_agent(row) if row else {"id": agent_id}


@router.put("/{agent_id}")
async def update_agent(
    agent_id: int,
    data: AgentCreate,
    user=Depends(get_current_user),
    agent_repo=Depends(get_agent_repository),
    model_repo=Depends(get_model_repository),
):
    """Редактировать агента."""
    row = await agent_repo.find_by_id(agent_id)
    if not row or row.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Агент не найден")

    if data.model_id:
        model = await model_repo.find_by_id(data.model_id)
        if not model or model.get("user_id") != user["id"]:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Модель не найдена")

    await agent_repo.update(
        agent_id=agent_id,
        user_id=user["id"],
        name=data.name.strip(),
        system_prompt=data.system_prompt or "",
        model_id=data.model_id,
    )

    updated = await agent_repo.find_by_id(agent_id)
    return serialize_agent(updated) if updated else {"id": agent_id}


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    user=Depends(get_current_user),
    agent_repo=Depends(get_agent_repository),
):
    """Удалить агента."""
    row = await agent_repo.find_by_id(agent_id)
    if not row or row.get("user_id") != user["id"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Агент не найден")

    await agent_repo.delete(agent_id, user["id"])
    return {"ok": True}


__all__ = ["router", "serialize_agent"]
