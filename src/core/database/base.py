"""Абстракция доступа к базе данных.

Интерфейс одинаков для SQLite (Docker) и Cloudflare D1 (Workers), поэтому
репозитории не знают о конкретном хранилище.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from core.database.migrations import migrate


@dataclass
class ExecuteResult:
    """Результат выполнения INSERT/UPDATE/DELETE."""

    lastrowid: Optional[int] = None
    rowcount: int = 0


class Database(ABC):
    """Асинхронный интерфейс работы с БД."""

    @abstractmethod
    async def execute(self, sql: str, params: Sequence[Any] = ()) -> ExecuteResult:
        """Выполнить одну SQL-команду (INSERT/UPDATE/DELETE/DDL)."""

    @abstractmethod
    async def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        """Получить первую строку результата или None."""

    @abstractmethod
    async def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        """Получить все строки результата."""

    async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]]) -> ExecuteResult:
        """Выполнить одну команду для набора параметров."""
        total = 0
        lastrowid = None
        for params in params_list:
            result = await self.execute(sql, params)
            total += result.rowcount
            lastrowid = result.lastrowid if result.lastrowid is not None else lastrowid
        return ExecuteResult(lastrowid=lastrowid, rowcount=total)

    async def initialize(self) -> None:
        """Создать/обновить схему БД."""
        await migrate(self)


__all__ = ["Database", "ExecuteResult", "migrate"]
