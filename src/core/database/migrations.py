"""Схема базы данных и миграции.

Один и тот же набор DDL-команд используется и для SQLite (Docker), и для
Cloudflare D1 (Workers) — обе платформы понимают базовый диалект SQLite.
"""

from __future__ import annotations

MIGRATIONS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        email      TEXT NOT NULL UNIQUE,
        name       TEXT NOT NULL,
        password   TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token      TEXT NOT NULL UNIQUE,
        expires_at TIMESTAMP NOT NULL,
        revoked    INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS providers (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name       TEXT NOT NULL,
        url        TEXT NOT NULL DEFAULT 'https://openrouter.ai/api/v1',
        api_key    TEXT NOT NULL DEFAULT '',
        extra      TEXT,
        is_default INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS models (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        provider_id INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
        name        TEXT NOT NULL,
        temperature REAL DEFAULT 0.7,
        max_tokens  INTEGER,
        extra       TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agents (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name          TEXT NOT NULL,
        system_prompt TEXT NOT NULL DEFAULT '',
        model_id      INTEGER REFERENCES models(id) ON DELETE SET NULL,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chats (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        agent_id   INTEGER REFERENCES agents(id) ON DELETE SET NULL,
        title      TEXT NOT NULL DEFAULT 'Новый чат',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id    INTEGER NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
        role       TEXT NOT NULL,
        content    TEXT NOT NULL,
        context    TEXT,
        usage      TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token)",
    "CREATE INDEX IF NOT EXISTS idx_providers_user ON providers(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_models_user ON models(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_agents_user ON agents(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_chats_user ON chats(user_id, updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, created_at)",
]


async def migrate(database) -> None:
    """Применить миграции (идемпотентно)."""
    for statement in MIGRATIONS:
        await database.execute(statement)


__all__ = ["MIGRATIONS", "migrate"]
