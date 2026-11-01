"""Схемы чатов и сообщений."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    """Создание чата."""

    title: str = Field(default="Новый чат", max_length=200)
    agent_id: Optional[int] = None


class ChatUpdate(BaseModel):
    """Обновление чата."""

    title: Optional[str] = Field(default=None, max_length=200)
    agent_id: Optional[int] = None


class MessageCreate(BaseModel):
    """Отправка сообщения агенту."""

    content: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    """Сообщение в ответе API."""

    id: Optional[int] = None
    chat_id: Optional[int] = None
    role: str
    content: str
    usage: Optional[Any] = None
    created_at: Optional[str] = None


class ChatOut(BaseModel):
    """Чат в ответе API."""

    id: int
    title: str
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    message_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatListOut(BaseModel):
    """Список чатов с общим количеством."""

    items: List[Dict[str, Any]]
    total: int
    limit: int = 50
    offset: int = 0


class ChatDetailOut(BaseModel):
    """Чат вместе с сообщениями."""

    chat: Dict[str, Any]
    messages: List[Dict[str, Any]]


__all__ = [
    "ChatCreate",
    "ChatUpdate",
    "MessageCreate",
    "MessageOut",
    "ChatOut",
    "ChatListOut",
    "ChatDetailOut",
]
