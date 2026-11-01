"""Схемы провайдеров."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

DEFAULT_PROVIDER_URL = "https://openrouter.ai/api/v1"


class ProviderCreate(BaseModel):
    """Создание/редактирование провайдера."""

    name: str = Field(..., min_length=1, max_length=120)
    url: str = Field(default=DEFAULT_PROVIDER_URL, max_length=500)
    api_key: str = Field(default="", max_length=500)
    only: List[str] = Field(default_factory=list)
    is_default: bool = False
    extra: Optional[Dict[str, Any]] = None

    @field_validator("only", mode="before")
    @classmethod
    def normalize_only(cls, value: Any) -> List[str]:
        """Принять список «через запятую» как строку."""
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, (list, tuple)):
            items: List[str] = []
            for entry in value:
                text = str(entry).strip()
                if text:
                    items.append(text)
            return items
        return []


class ProviderOut(BaseModel):
    """Провайдер в ответе API (api_key скрывается)."""

    id: int
    name: str
    url: str
    api_key: str = ""
    only: List[str] = Field(default_factory=list)
    is_default: bool = False
    created_at: Optional[str] = None


__all__ = ["ProviderCreate", "ProviderOut", "DEFAULT_PROVIDER_URL"]
