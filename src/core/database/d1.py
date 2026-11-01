"""Реализация доступа к БД на базе Cloudflare D1 (Workers)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from core.database.base import Database, ExecuteResult

D1_BINDING_NAME = "DB"


class D1Database(Database):
    """Асинхронная обёртка над Cloudflare D1."""

    def __init__(self, env: Any, binding: str = D1_BINDING_NAME) -> None:
        self._env = env
        self._binding = binding
        self._database = None

    # ------------------------------------------------------------------
    # Внутреннее
    # ------------------------------------------------------------------
    def _get_database(self) -> Any:
        if self._database is None:
            database = getattr(self._env, self._binding, None)
            if database is None:
                raise RuntimeError(
                    f"Не найден binding '{self._binding}' для Cloudflare D1. "
                    "Добавьте d1_databases в wrangler.jsonc"
                )
            self._database = database
        return self._database

    def _prepare(self, sql: str, params: Sequence[Any]) -> Any:
        statement = self._get_database().prepare(sql)
        values = [value for value in params]
        if values:
            statement = statement.bind(*values)
        return statement

    # ------------------------------------------------------------------
    # Запросы
    # ------------------------------------------------------------------
    async def execute(self, sql: str, params: Sequence[Any] = ()) -> ExecuteResult:
        result = await self._prepare(sql, params).run()
        meta = getattr(result, "meta", None)
        return ExecuteResult(
            lastrowid=getattr(meta, "last_row_id", None) if meta else None,
            rowcount=getattr(meta, "changes", 0) if meta else 0,
        )

    async def fetch_one(self, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        row = await self._prepare(sql, params).first()
        return dict(row) if row else None

    async def fetch_all(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        result = await self._prepare(sql, params).all()
        results = result.get("results", []) if isinstance(result, dict) else result
        return [dict(row) for row in results]


__all__ = ["D1Database", "D1_BINDING_NAME"]
