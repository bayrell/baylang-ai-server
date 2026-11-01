"""Реализация доступа к БД на базе SQLite (Docker/локальная разработка)."""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Sequence

from core.database.base import Database, ExecuteResult

DEFAULT_DATABASE_PATH = os.environ.get("DATABASE_PATH", "./data/baylang.sqlite3")


class SqliteDatabase(Database):
    """Асинхронная обёртка над `sqlite3` с одним соединением на процесс."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or DEFAULT_DATABASE_PATH
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Соединение
    # ------------------------------------------------------------------
    def connect(self) -> sqlite3.Connection:
        """Получить (или создать) соединение с БД."""
        with self._lock:
            if self._connection is None:
                if self.path not in (":memory:", "") and not self.path.startswith("file:"):
                    directory = os.path.dirname(os.path.abspath(self.path))
                    if directory:
                        os.makedirs(directory, exist_ok=True)

                connection = sqlite3.connect(
                    self.path,
                    check_same_thread=False,
                    isolation_level=None,  # autocommit
                )
                connection.row_factory = sqlite3.Row
                connection.execute("PRAGMA foreign_keys = ON")
                self._connection = connection
            return self._connection

    def close(self) -> None:
        """Закрыть соединение."""
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    # ------------------------------------------------------------------
    # Запросы
    # ------------------------------------------------------------------
    async def execute(self, sql: str, params: Sequence[Any] = ()) -> ExecuteResult:
        with self._lock:
            connection = self.connect()
            cursor = connection.execute(sql, tuple(params))
            result = ExecuteResult(
                lastrowid=cursor.lastrowid,
                rowcount=cursor.rowcount if cursor.rowcount is not None else 0,
            )
            cursor.close()
        return result

    async def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        with self._lock:
            connection = self.connect()
            cursor = connection.execute(sql, tuple(params))
            row = cursor.fetchone()
            cursor.close()
        return dict(row) if row is not None else None

    async def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        with self._lock:
            connection = self.connect()
            cursor = connection.execute(sql, tuple(params))
            rows = cursor.fetchall()
            cursor.close()
        return [dict(row) for row in rows]


__all__ = ["SqliteDatabase", "DEFAULT_DATABASE_PATH"]
