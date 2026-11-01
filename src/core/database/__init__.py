"""Доступ к базе данных: общий интерфейс, SQLite и Cloudflare D1."""

from core.database.base import Database, ExecuteResult
from core.database.d1 import D1Database
from core.database.migrations import MIGRATIONS, migrate
from core.database.sqlite import DEFAULT_DATABASE_PATH, SqliteDatabase

__all__ = [
    "Database",
    "ExecuteResult",
    "MIGRATIONS",
    "migrate",
    "SqliteDatabase",
    "D1Database",
    "DEFAULT_DATABASE_PATH",
]
