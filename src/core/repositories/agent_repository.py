"""Record-репозиторий для агентов (персон бота)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.repositories.base import BaseRepository


class AgentRepository(BaseRepository):
    """Record-репозиторий для работы с агентами."""

    table = "agents"

    async def create(
        self,
        user_id: int,
        name: str,
        system_prompt: str = "",
        model_id: Optional[int] = None,
    ) -> int:
        """Создать агента."""
        result = await self.execute(
            """
            INSERT INTO agents (user_id, name, system_prompt, model_id)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, name, system_prompt, model_id),
        )
        return result.lastrowid

    async def find_by_id(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Найти агента по id."""
        return await self.fetch_one(
            "SELECT * FROM agents WHERE id = ?",
            (agent_id,),
        )

    async def find_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Список агентов пользователя."""
        return await self.fetch_all(
            """
            SELECT a.*, m.name AS model_name
            FROM agents a
            LEFT JOIN models m ON m.id = a.model_id
            WHERE a.user_id = ?
            ORDER BY a.id ASC
            """,
            (user_id,),
        )

    async def update(
        self,
        agent_id: int,
        user_id: int,
        name: str,
        system_prompt: str,
        model_id: Optional[int],
    ) -> int:
        """Обновить агента."""
        result = await self.execute(
            """
            UPDATE agents
            SET name = ?, system_prompt = ?, model_id = ?
            WHERE id = ? AND user_id = ?
            """,
            (name, system_prompt, model_id, agent_id, user_id),
        )
        return result.rowcount

    async def delete(self, agent_id: int, user_id: int) -> int:
        """Удалить агента пользователя."""
        result = await self.execute(
            "DELETE FROM agents WHERE id = ? AND user_id = ?",
            (agent_id, user_id),
        )
        return result.rowcount


__all__ = ["AgentRepository"]
