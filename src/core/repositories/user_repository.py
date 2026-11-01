"""Record-репозиторий для пользователей и refresh-токенов."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Record-репозиторий для работы с пользователями."""

    table = "users"

    # ------------------------------------------------------------------
    # Пользователи
    # ------------------------------------------------------------------
    async def create(self, email: str, name: str, password_hash: str) -> int:
        """Создать пользователя и вернуть его id."""
        result = await self.execute(
            """
            INSERT INTO users (email, name, password)
            VALUES (?, ?, ?)
            """,
            (email, name, password_hash),
        )
        return result.lastrowid

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Найти пользователя по email."""
        return await self.fetch_one(
            "SELECT * FROM users WHERE email = ?",
            (email.lower(),),
        )

    async def find_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Найти пользователя по id."""
        return await self.fetch_one(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        )

    async def update_name(self, user_id: int, name: str) -> None:
        """Обновить имя пользователя."""
        await self.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (name, user_id),
        )

    async def update_password(self, user_id: int, password_hash: str) -> None:
        """Обновить пароль пользователя."""
        await self.execute(
            "UPDATE users SET password = ? WHERE id = ?",
            (password_hash, user_id),
        )

    async def delete(self, user_id: int) -> None:
        """Удалить пользователя вместе со связанными данными."""
        await self.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # ------------------------------------------------------------------
    # Refresh-токены
    # ------------------------------------------------------------------
    async def save_refresh_token(self, user_id: int, token: str, expires_at: str) -> None:
        """Сохранить выданный refresh-токен."""
        await self.execute(
            """
            INSERT INTO refresh_tokens (user_id, token, expires_at, revoked)
            VALUES (?, ?, ?, 0)
            """,
            (user_id, token, expires_at),
        )

    async def find_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Получить запись refresh-токена."""
        return await self.fetch_one(
            "SELECT * FROM refresh_tokens WHERE token = ?",
            (token,),
        )

    async def revoke_refresh_token(self, token: str) -> None:
        """Пометить refresh-токен отозванным."""
        await self.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE token = ?",
            (token,),
        )

    async def revoke_user_tokens(self, user_id: int) -> None:
        """Отозвать все refresh-токены пользователя."""
        await self.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?",
            (user_id,),
        )

    async def delete_expired_tokens(self) -> int:
        """Удалить просроченные и отозванные токены."""
        now = datetime.now(timezone.utc).isoformat()
        result = await self.execute(
            "DELETE FROM refresh_tokens WHERE expires_at < ? OR revoked = 1",
            (now,),
        )
        return result.rowcount

    async def list_user_tokens(self, user_id: int) -> List[Dict[str, Any]]:
        """Список активных refresh-токенов пользователя."""
        return await self.fetch_all(
            "SELECT * FROM refresh_tokens WHERE user_id = ? AND revoked = 0",
            (user_id,),
        )


__all__ = ["UserRepository"]
