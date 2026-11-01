"""Record-репозиторий для сообщений чата."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.repositories.base import BaseRepository


class MessageRepository(BaseRepository):
    """Record-репозиторий для работы с сообщениями."""

    table = "messages"

    async def create(
        self,
        chat_id: int,
        role: str,
        content: str,
        context: Optional[str] = None,
        usage: Optional[str] = None,
    ) -> int:
        """Создать сообщение."""
        result = await self.execute(
            """
            INSERT INTO messages (chat_id, role, content, context, usage)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, role, content, context, usage),
        )
        return result.lastrowid

    async def find_by_id(self, message_id: int) -> Optional[Dict[str, Any]]:
        """Найти сообщение по id."""
        return await self.fetch_one(
            "SELECT * FROM messages WHERE id = ?",
            (message_id,),
        )

    async def list_by_chat(self, chat_id: int, limit: int = 500) -> List[Dict[str, Any]]:
        """Список сообщений чата (по возрастанию времени)."""
        return await self.fetch_all(
            """
            SELECT id, chat_id, role, content, usage, created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (chat_id, max(1, min(int(limit), 2000))),
        )

    async def find_last_with_context(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Последнее сообщение с сохранённым контекстом pydantic-ai."""
        return await self.fetch_one(
            """
            SELECT * FROM messages
            WHERE chat_id = ? AND context IS NOT NULL AND context != ''
            ORDER BY id DESC
            LIMIT 1
            """,
            (chat_id,),
        )

    async def count_by_chat(self, chat_id: int) -> int:
        """Количество сообщений в чате."""
        row = await self.fetch_one(
            "SELECT COUNT(*) AS total FROM messages WHERE chat_id = ?",
            (chat_id,),
        )
        return int(row["total"]) if row else 0

    async def delete_by_chat(self, chat_id: int) -> int:
        """Удалить все сообщения чата."""
        result = await self.execute(
            "DELETE FROM messages WHERE chat_id = ?",
            (chat_id,),
        )
        return result.rowcount


__all__ = ["MessageRepository"]
