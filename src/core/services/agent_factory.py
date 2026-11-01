"""Фабрика агентов pydantic-ai: «персона» = системный промпт + модель."""

from __future__ import annotations

import os

os.environ["PYDANTIC_AI_NO_BANNER"] = "1"

from typing import Any, Dict, Optional  # noqa: E402

from core.services.model_service import (  # noqa: E402
    APP_TITLE,
    APP_URL,
    build_model,
)

DEFAULT_SYSTEM_PROMPT = "Ты — полезный ассистент. Отвечай кратко и по делу."
DEFAULT_RETRIES = 10


class AgentError(RuntimeError):
    """Ошибка сборки агента (нет модели, нет провайдера и т.п.)."""


class AgentFactory:
    """Собирает агента по настройкам из БД."""

    def __init__(self, agent_repo, model_repo, provider_repo) -> None:
        self.agent_repo = agent_repo
        self.model_repo = model_repo
        self.provider_repo = provider_repo

    async def build(self, agent_id: Optional[int], user_id: Optional[int] = None) -> Any:
        """Собрать агента.

        Если `agent_id` не задан, берётся первый агент пользователя.
        """
        from pydantic_ai import Agent

        agent_row = await self._resolve_agent(agent_id, user_id)
        if not agent_row:
            raise AgentError("Агент не найден")

        model_row = None
        if agent_row.get("model_id"):
            model_row = await self.model_repo.find_by_id(agent_row["model_id"])

        if not model_row:
            raise AgentError("У агента не выбрана модель")

        provider_row = await self.provider_repo.find_by_id(model_row["provider_id"])
        if not provider_row:
            raise AgentError("Провайдер модели не найден")

        model = build_model(model_row, provider_row)

        return Agent(
            model,
            system_prompt=agent_row.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
            retries=DEFAULT_RETRIES,
        )

    async def _resolve_agent(
        self,
        agent_id: Optional[int],
        user_id: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """Найти запись агента: по id либо первого агента пользователя."""
        if agent_id:
            row = await self.agent_repo.find_by_id(agent_id)
            if row and user_id is not None and row.get("user_id") != user_id:
                return None
            return row

        if user_id is None:
            return None

        agents = await self.agent_repo.find_by_user(user_id)
        return agents[0] if agents else None


__all__ = [
    "AgentFactory",
    "AgentError",
    "DEFAULT_SYSTEM_PROMPT",
    "APP_URL",
    "APP_TITLE",
]
