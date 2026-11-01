"""Схемы моделей."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    """Создание/редактирование модели."""

    provider_id: int
    name: str = Field(..., min_length=1, max_length=200, examples=["anthropic/claude-3.5-sonnet"])
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    extra: Optional[Dict[str, Any]] = None


class ModelOut(BaseModel):
    """Модель в ответе API."""

    id: int
    provider_id: int
    provider_name: Optional[str] = None
    name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


__all__ = ["ModelCreate", "ModelOut"]
