"""Точка входа для Cloudflare Workers."""

from __future__ import annotations

import os
import sys

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

try:  # pragma: no cover - зависит от способа запуска
    from src.app import create_cloudflare_app
except ImportError:  # pragma: no cover
    from app import create_cloudflare_app

from workers import WorkerEntrypoint  # noqa: E402


class Default(WorkerEntrypoint):
    """Worker-entrypoint с ASGI-приложением FastAPI."""

    def __init__(self, *args, **kwargs):
        WorkerEntrypoint.__init__(self, *args, **kwargs)
        self.app = create_cloudflare_app(self.env)
        self._ready = False

    async def _ensure_schema(self) -> None:
        """Создать схему D1 при первом запросе."""
        if self._ready:
            return

        from core.container import container

        database = container.get("database")
        await database.initialize()
        self._ready = True

    async def fetch(self, request):
        import asgi

        await self._ensure_schema()
        return await asgi.fetch(self.app, request.js_object, self.env)


__all__ = ["Default", "create_cloudflare_app"]
