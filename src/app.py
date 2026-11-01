"""Точка входа для Docker: `uvicorn app:create_app --factory`.

Тот же модуль используется как fallback для Cloudflare Workers, поэтому
корень `src` добавляется в `sys.path` — тогда пакет `core` доступен
независимо от текущей рабочей директории.
"""

from __future__ import annotations

import os
import sys

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from core.app import create_app, create_cloudflare_app  # noqa: E402,F401  (re-export)


def main() -> None:
    """Запустить приложение через uvicorn (для `python app.py`)."""
    import uvicorn

    uvicorn.run(
        create_app(),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
