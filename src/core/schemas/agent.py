"""Схемы агентов."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Создание/редактирование агента."""

    name: str = Field(..., min_length=1, max_length=120)
    system_prompt: str = Field(default="", max_length=8000)
    model_id: Optional[int] = None


class AgentOut(BaseModel):
    """Агент в ответе API."""

    id: int
    name: str
    system_prompt: str = ""
    model_id: Optional[int] = None
    model_name: Optional[str] = None
    created_at: Optional[str] = None


__all__ = ["AgentCreate", "AgentOut"]
