"""Сервис провайдеров: работа с полем `only` (список upstream-провайдеров)."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

OPENROUTER_NAME = "OpenRouter"
OPENROUTER_URL = "https://openrouter.ai/api/v1"


def parse_only(value: Any) -> List[str]:
    """Преобразовать «список через запятую» в список строк."""
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Iterable):
        items: List[str] = []
        for entry in value:
            text = str(entry).strip()
            if text:
                items.append(text)
        return items
    return []


def load_extra(raw: Optional[str]) -> Dict[str, Any]:
    """Разобрать JSON-поле `extra`."""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def dump_extra(only: Any = None, extra: Optional[Dict[str, Any]] = None) -> str:
    """Собрать JSON-поле `extra` из списка `only` и дополнительных полей."""
    payload: Dict[str, Any] = dict(extra or {})
    payload["only"] = parse_only(only)
    return json.dumps(payload, ensure_ascii=False)


def build_openrouter_config(provider_row: Dict[str, Any]) -> Dict[str, Any]:
    """Собрать `OpenRouterProviderConfig` из записи провайдера."""
    config: Dict[str, Any] = {}
    extra = load_extra(provider_row.get("extra"))
    only = parse_only(extra.get("only"))
    if only:
        config["only"] = only
    return config


def is_openrouter(provider_row: Dict[str, Any]) -> bool:
    """Определить, что провайдер — OpenRouter."""
    name = str(provider_row.get("name") or "").strip().lower()
    url = str(provider_row.get("url") or "").strip().lower()
    return name == OPENROUTER_NAME.lower() or "openrouter.ai" in url


def serialize_provider(row: Dict[str, Any], reveal_key: bool = False) -> Dict[str, Any]:
    """Преобразовать строку БД в ответ API."""
    extra = load_extra(row.get("extra"))
    api_key = row.get("api_key") or ""
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "url": row.get("url"),
        "api_key": api_key if reveal_key else ("*" * 8 if api_key else ""),
        "has_api_key": bool(api_key),
        "only": parse_only(extra.get("only")),
        "is_default": bool(row.get("is_default")),
        "created_at": row.get("created_at"),
    }


async def create_default_provider(provider_repo, user_id: int) -> int:
    """Создать провайдера OpenRouter по умолчанию для нового пользователя."""
    return await provider_repo.create(
        user_id=user_id,
        name=OPENROUTER_NAME,
        url=OPENROUTER_URL,
        api_key="",  # пользователь заполняет ключ сам
        extra=dump_extra([]),
        is_default=True,
    )


__all__ = [
    "OPENROUTER_NAME",
    "OPENROUTER_URL",
    "parse_only",
    "load_extra",
    "dump_extra",
    "build_openrouter_config",
    "is_openrouter",
    "serialize_provider",
    "create_default_provider",
]
