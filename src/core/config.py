"""Доступ к переменным окружения (os.environ или Cloudflare bindings)."""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping, Optional


class Env:
    """Унифицированный доступ к окружению.

    Поддерживает как обычный словарь (`os.environ`), так и объект bindings
    Cloudflare Workers, где переменные доступны через атрибуты.
    """

    def __init__(self, values: Optional[Any] = None) -> None:
        self._values: Dict[str, Any] = {}
        self._object: Optional[Any] = None

        if values is None:
            self._values = dict(os.environ)
        elif isinstance(values, Mapping):
            self._values = dict(values)
        else:
            self._object = values

    def get(self, key: str, default: Any = None) -> Any:
        """Вернуть значение или `default`, если переменной нет."""
        if self._object is not None:
            value = getattr(self._object, key, None)
            return default if value is None else value

        value = self._values.get(key)
        return default if value in (None, "") else value

    def require(self, key: str) -> Any:
        """Вернуть значение или бросить исключение, если переменной нет."""
        value = self.get(key)
        if value is None:
            raise RuntimeError(f"Переменная окружения '{key}' обязательна")
        return value

    def get_int(self, key: str, default: int = 0) -> int:
        """Получить значение как целое число."""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Получить значение как булево."""
        value = self.get(key)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    def all(self) -> Dict[str, Any]:
        """Все значения окружения в виде словаря."""
        if self._object is not None:
            return {
                name: getattr(self._object, name)
                for name in dir(self._object)
                if not name.startswith("_") and not callable(getattr(self._object, name, None))
            }
        return dict(self._values)

    def __contains__(self, key: str) -> bool:  # pragma: no cover - удобство
        return self.get(key) is not None

    def __repr__(self) -> str:  # pragma: no cover - отладка
        return f"<Env keys={len(self.all())}>"


__all__ = ["Env"]
