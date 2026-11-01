"""Базовый класс Record-репозитория."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from core.database.base import Database


class BaseRepository:
    """Record-репозиторий: инкапсулирует SQL-запросы к одной таблице."""

    table: str = ""

    def __init__(self, database: Database) -> None:
        self.database = database

    async def execute(self, sql: str, params: Sequence[Any] = ()) -> Any:
        """Выполнить SQL-команду."""
        return await self.database.execute(sql, params)

    async def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        """Получить одну строку."""
        return await self.database.fetch_one(sql, params)

    async def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> Any:
        """Получить список строк."""
        return await self.database.fetch_all(sql, params)


__all__ = ["BaseRepository"]
