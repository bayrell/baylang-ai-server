"""Record-репозиторий для чатов."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.repositories.base import BaseRepository

DEFAULT_CHAT_TITLE = "Новый чат"
DEFAULT_LIMIT = 50


class ChatRepository(BaseRepository):
    """Record-репозиторий для работы с чатами."""

    table = "chats"

    async def create(
        self,
        user_id: int,
        title: str = DEFAULT_CHAT_TITLE,
        agent_id: Optional[int] = None,
    ) -> int:
        """Создать чат."""
        result = await self.execute(
            """
            INSERT INTO chats (user_id, title, agent_id)
            VALUES (?, ?, ?)
            """,
            (user_id, title, agent_id),
        )
        return result.lastrowid

    async def find_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Найти чат по id (без проверки владельца)."""
        return await self.fetch_one(
            """
            SELECT c.*, a.name AS agent_name
            FROM chats c
            LEFT JOIN agents a ON a.id = c.agent_id
            WHERE c.id = ?
            """,
            (chat_id,),
        )

    async def find_owned(self, chat_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Найти чат, принадлежащий пользователю."""
        return await self.fetch_one(
            """
            SELECT c.*, a.name AS agent_name
            FROM chats c
            LEFT JOIN agents a ON a.id = c.agent_id
            WHERE c.id = ? AND c.user_id = ?
            """,
            (chat_id, user_id),
        )

    async def is_owned(self, chat_id: int, user_id: int) -> bool:
        """Проверить, принадлежит ли чат пользователю."""
        row = await self.fetch_one(
            "SELECT id FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        return row is not None

    async def list(
        self,
        user_id: int,
        query: str = "",
        filter: str = "all",
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Список чатов пользователя с поиском и фильтром по дате."""
        where, params = self._build_filters(user_id, query, filter)
        params.extend([max(1, min(int(limit), 200)), max(0, int(offset))])

        return await self.fetch_all(
            f"""
            SELECT c.*, a.name AS agent_name,
                   (SELECT COUNT(*) FROM messages m WHERE m.chat_id = c.id) AS message_count
            FROM chats c
            LEFT JOIN agents a ON a.id = c.agent_id
            {where}
            ORDER BY c.updated_at DESC, c.id DESC
            LIMIT ? OFFSET ?
            """,
            params,
        )

    async def count(self, user_id: int, query: str = "", filter: str = "all") -> int:
        """Количество чатов по текущему фильтру."""
        where, params = self._build_filters(user_id, query, filter)
        row = await self.fetch_one(
            f"SELECT COUNT(*) AS total FROM chats c {where}",
            params,
        )
        return int(row["total"]) if row else 0

    async def touch(self, chat_id: int, title: Optional[str] = None) -> None:
        """Обновить дату обновления (и при необходимости заголовок) чата."""
        if title:
            await self.execute(
                """
                UPDATE chats
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, chat_id),
            )
            return

        await self.execute(
            "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (chat_id,),
        )

    async def rename(self, chat_id: int, user_id: int, title: str) -> int:
        """Переименовать чат."""
        result = await self.execute(
            "UPDATE chats SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (title, chat_id, user_id),
        )
        return result.rowcount

    async def set_agent(self, chat_id: int, user_id: int, agent_id: Optional[int]) -> int:
        """Привязать чат к другому агенту."""
        result = await self.execute(
            "UPDATE chats SET agent_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (agent_id, chat_id, user_id),
        )
        return result.rowcount

    async def delete(self, chat_id: int, user_id: int) -> int:
        """Удалить чат пользователя."""
        result = await self.execute(
            "DELETE FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, user_id),
        )
        return result.rowcount

    # ------------------------------------------------------------------
    # Внутреннее
    # ------------------------------------------------------------------
    @staticmethod
    def _build_filters(user_id: int, query: str, filter: str) -> tuple:
        """Собрать WHERE-условие для поиска и фильтрации."""
        conditions = ["c.user_id = ?"]
        params: List[Any] = [user_id]

        query = (query or "").strip()
        if query:
            conditions.append("LOWER(c.title) LIKE ?")
            params.append(f"%{query.lower()}%")

        filter = (filter or "all").strip().lower()
        if filter == "today":
            conditions.append("date(c.updated_at) = date('now')")
        elif filter == "week":
            conditions.append("c.updated_at >= datetime('now', '-7 days')")
        elif filter == "month":
            conditions.append("c.updated_at >= datetime('now', '-30 days')")

        return "WHERE " + " AND ".join(conditions), params


__all__ = ["ChatRepository", "DEFAULT_CHAT_TITLE", "DEFAULT_LIMIT"]
