"""Простой DI-контейнер проекта BayLang AI.

Использование:

    container.register("app", lambda: FastAPI())          # transient
    container.singleton("database", lambda c: SqliteDatabase())
    database = container.get("database")

Фабрика может принимать контейнер (`lambda c: ...`) или не принимать аргументов
(`lambda: ...`) — вызов разбирается автоматически по сигнатуре.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict

Factory = Callable[..., Any]


class Container:
    """Контейнер зависимостей с поддержкой transient- и singleton-регистраций."""

    def __init__(self) -> None:
        self._factories: Dict[str, Factory] = {}
        self._singletons: Dict[str, bool] = {}
        self._instances: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Регистрация
    # ------------------------------------------------------------------
    def register(self, name: str, factory: Factory) -> None:
        """Transient-регистрация: объект создаётся при каждом вызове get()."""
        self._factories[name] = factory
        self._singletons[name] = False
        self._instances.pop(name, None)

    def singleton(self, name: str, factory: Factory) -> None:
        """Singleton-регистрация: объект создаётся один раз и кэшируется."""
        self._factories[name] = factory
        self._singletons[name] = True
        self._instances.pop(name, None)

    def instance(self, name: str, value: Any) -> None:
        """Заранее созданный объект (удобно для тестов и моков)."""
        self._factories[name] = lambda c: value
        self._singletons[name] = True
        self._instances[name] = value

    # ------------------------------------------------------------------
    # Доступ
    # ------------------------------------------------------------------
    def has(self, name: str) -> bool:
        """Проверить, зарегистрирована ли зависимость."""
        return name in self._factories

    def get(self, name: str) -> Any:
        """Получить объект по имени (создать, если ещё не создан)."""
        if name in self._instances:
            return self._instances[name]

        factory = self._factories.get(name)
        if factory is None:
            raise KeyError(f"Зависимость '{name}' не зарегистрирована в контейнере")

        instance = self._call(factory)
        if self._singletons.get(name):
            self._instances[name] = instance
        return instance

    # ------------------------------------------------------------------
    # Служебное
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Очистить контейнер (используется в тестах)."""
        self._factories.clear()
        self._singletons.clear()
        self._instances.clear()

    def _call(self, factory: Factory) -> Any:
        """Вызвать фабрику, подставив контейнер, если он принимает аргумент."""
        try:
            signature = inspect.signature(factory)
        except (TypeError, ValueError):  # pragma: no cover - builtins без сигнатуры
            return factory(self)

        positional = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        accepts_varargs = any(
            parameter.kind == inspect.Parameter.VAR_POSITIONAL
            for parameter in signature.parameters.values()
        )

        if positional or accepts_varargs:
            return factory(self)
        return factory()


#: Глобальный контейнер приложения.
container = Container()

__all__ = ["Container", "container", "Factory"]
