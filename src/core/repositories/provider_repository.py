"""Record-репозиторий для провайдеров (OpenRouter и прочие LLM-сервисы)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.repositories.base import BaseRepository


class ProviderRepository(BaseRepository):
    """Record-репозиторий для работы с провайдерами."""

    table = "providers"

    async def create(
        self,
        user_id: int,
        name: str,
        url: str,
        api_key: str = "",
        extra: Optional[str] = None,
        is_default: bool = False,
    ) -> int:
        """Создать провайдера."""
        result = await self.execute(
            """
            INSERT INTO providers (user_id, name, url, api_key, extra, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, url, api_key, extra, 1 if is_default else 0),
        )
        return result.lastrowid

    async def find_by_id(self, provider_id: int) -> Optional[Dict[str, Any]]:
        """Найти провайдера по id."""
        return await self.fetch_one(
            "SELECT * FROM providers WHERE id = ?",
            (provider_id,),
        )

    async def find_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Список провайдеров пользователя (по умолчанию — первым)."""
        return await self.fetch_all(
            """
            SELECT * FROM providers
            WHERE user_id = ?
            ORDER BY is_default DESC, id ASC
            """,
            (user_id,),
        )

    async def find_default(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Провайдер по умолчанию пользователя."""
        return await self.fetch_one(
            """
            SELECT * FROM providers
            WHERE user_id = ? AND is_default = 1
            ORDER BY id ASC
            LIMIT 1
            """,
            (user_id,),
        )

    async def update(
        self,
        provider_id: int,
        user_id: int,
        name: str,
        url: str,
        api_key: str,
        extra: Optional[str],
        is_default: bool,
    ) -> int:
        """Обновить провайдера. Возвращает количество изменённых строк."""
        if is_default:
            await self.reset_default(user_id)

        result = await self.execute(
            """
            UPDATE providers
            SET name = ?, url = ?, api_key = ?, extra = ?, is_default = ?
            WHERE id = ? AND user_id = ?
            """,
            (name, url, api_key, extra, 1 if is_default else 0, provider_id, user_id),
        )
        return result.rowcount

    async def reset_default(self, user_id: int) -> None:
        """Снять флаг «по умолчанию» со всех провайдеров пользователя."""
        await self.execute(
            "UPDATE providers SET is_default = 0 WHERE user_id = ?",
            (user_id,),
        )

    async def delete(self, provider_id: int, user_id: int) -> int:
        """Удалить провайдера пользователя."""
        result = await self.execute(
            "DELETE FROM providers WHERE id = ? AND user_id = ?",
            (provider_id, user_id),
        )
        return result.rowcount


__all__ = ["ProviderRepository"]
