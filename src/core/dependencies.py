"""Зависимости FastAPI: репозитории, сервисы и текущий пользователь."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.container import container
from core.security import decode_token

security = HTTPBearer(auto_error=False, description="JWT access-токен")


# ----------------------------------------------------------------------
# Зависимости контейнера
# ----------------------------------------------------------------------
def get_user_repository():
    """Репозиторий пользователей."""
    return container.get("user_repository")


def get_provider_repository():
    """Репозиторий провайдеров."""
    return container.get("provider_repository")


def get_model_repository():
    """Репозиторий моделей."""
    return container.get("model_repository")


def get_agent_repository():
    """Репозиторий агентов."""
    return container.get("agent_repository")


def get_chat_repository():
    """Репозиторий чатов."""
    return container.get("chat_repository")


def get_message_repository():
    """Репозиторий сообщений."""
    return container.get("message_repository")


def get_chat_service():
    """Сервис чата."""
    return container.get("chat_service")


def get_agent_factory():
    """Фабрика агентов."""
    return container.get("agent_factory")


# ----------------------------------------------------------------------
# Авторизация
# ----------------------------------------------------------------------
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo=Depends(get_user_repository),
) -> Dict[str, Any]:
    """Текущий пользователь по JWT access-токену."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Не авторизован")

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return user


__all__ = [
    "security",
    "get_user_repository",
    "get_provider_repository",
    "get_model_repository",
    "get_agent_repository",
    "get_chat_repository",
    "get_message_repository",
    "get_chat_service",
    "get_agent_factory",
    "get_current_user",
]
