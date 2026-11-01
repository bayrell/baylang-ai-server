"""Сборка LLM-моделей pydantic-ai из настроек пользователя."""

from __future__ import annotations

from typing import Any, Dict

from core.services.provider_service import (
    build_openrouter_config,
    is_openrouter,
    load_extra,
)

APP_URL = "https://baylang.com/"
APP_TITLE = "BayLang AI"


def _model_settings(model_row: Dict[str, Any]) -> Dict[str, Any]:
    """Параметры генерации из записи модели."""
    settings: Dict[str, Any] = {}

    temperature = model_row.get("temperature")
    if temperature is not None:
        settings["temperature"] = float(temperature)

    max_tokens = model_row.get("max_tokens")
    if max_tokens:
        settings["max_tokens"] = int(max_tokens)

    extra = load_extra(model_row.get("extra"))
    for key, value in extra.items():
        if key == "only":
            continue
        settings[key] = value

    return settings


def build_openrouter_model(model_row: Dict[str, Any], provider_row: Dict[str, Any]) -> Any:
    """Собрать `OpenRouterModel` по настройкам модели и провайдера."""
    from pydantic_ai.models.openrouter import OpenRouterModel
    from pydantic_ai.providers.openrouter import OpenRouterProvider

    settings = _model_settings(model_row)
    config = build_openrouter_config(provider_row)

    model_settings: Dict[str, Any] = {
        "openrouter_cache_instructions": True,
        "openrouter_cache_messages": True,
        "openrouter_cache_tool_definitions": True,
    }
    if config:
        model_settings["openrouter_provider"] = config
    model_settings.update(settings)

    provider = OpenRouterProvider(
        api_key=provider_row.get("api_key") or "",
        app_url=APP_URL,
        app_title=APP_TITLE,
    )

    try:
        from pydantic_ai.models.openrouter import OpenRouterModelSettings

        return OpenRouterModel(
            model_row["name"],
            provider=provider,
            settings=OpenRouterModelSettings(**model_settings),
        )
    except (TypeError, ValueError):  # pragma: no cover - старая версия pydantic-ai
        return OpenRouterModel(
            model_row["name"],
            provider=provider,
            settings=settings or None,
        )


def build_openai_compatible_model(model_row: Dict[str, Any], provider_row: Dict[str, Any]) -> Any:
    """Собрать модель для любого OpenAI-совместимого endpoint (OpenAI, Groq, и т.п.)."""
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    settings = _model_settings(model_row)
    provider = OpenAIProvider(
        api_key=provider_row.get("api_key") or "",
        base_url=provider_row.get("url") or None,
    )
    return OpenAIChatModel(model_row["name"], provider=provider, settings=settings or None)


def build_model(model_row: Dict[str, Any], provider_row: Dict[str, Any]) -> Any:
    """Собрать модель pydantic-ai по типу провайдера."""
    if is_openrouter(provider_row):
        return build_openrouter_model(model_row, provider_row)
    return build_openai_compatible_model(model_row, provider_row)


__all__ = [
    "APP_URL",
    "APP_TITLE",
    "build_model",
    "build_openrouter_model",
    "build_openai_compatible_model",
]
