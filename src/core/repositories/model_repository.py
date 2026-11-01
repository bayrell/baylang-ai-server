"""Record-репозиторий для моделей."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.repositories.base import BaseRepository


class ModelRepository(BaseRepository):
    """Record-репозиторий для работы с моделями."""

    table = "models"

    async def create(
        self,
        user_id: int,
        provider_id: int,
        name: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        extra: Optional[str] = None,
    ) -> int:
        """Создать модель."""
        result = await self.execute(
            """
            INSERT INTO models (user_id, provider_id, name, temperature, max_tokens, extra)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, provider_id, name, temperature, max_tokens, extra),
        )
        return result.lastrowid

    async def find_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Найти модель по id."""
        return await self.fetch_one(
            "SELECT * FROM models WHERE id = ?",
            (model_id,),
        )

    async def find_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Список моделей пользователя."""
        return await self.fetch_all(
            """
            SELECT m.*, p.name AS provider_name
            FROM models m
            LEFT JOIN providers p ON p.id = m.provider_id
            WHERE m.user_id = ?
            ORDER BY m.id ASC
            """,
            (user_id,),
        )

    async def update(
        self,
        model_id: int,
        user_id: int,
        provider_id: int,
        name: str,
        temperature: float,
        max_tokens: Optional[int],
        extra: Optional[str],
    ) -> int:
        """Обновить модель."""
        result = await self.execute(
            """
            UPDATE models
            SET provider_id = ?, name = ?, temperature = ?, max_tokens = ?, extra = ?
            WHERE id = ? AND user_id = ?
            """,
            (provider_id, name, temperature, max_tokens, extra, model_id, user_id),
        )
        return result.rowcount

    async def delete(self, model_id: int, user_id: int) -> int:
        """Удалить модель пользователя."""
        result = await self.execute(
            "DELETE FROM models WHERE id = ? AND user_id = ?",
            (model_id, user_id),
        )
        return result.rowcount


__all__ = ["ModelRepository"]
