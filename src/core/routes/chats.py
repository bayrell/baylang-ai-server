"""Маршруты чатов и сообщений."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from core.dependencies import (
    get_chat_repository,
    get_chat_service,
    get_current_user,
    get_message_repository,
)
from core.repositories.chat_repository import DEFAULT_LIMIT
from core.schemas.chat import ChatCreate, ChatUpdate, MessageCreate

router = APIRouter(prefix="/api/chats", tags=["chats"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.get("")
async def list_chats(
    q: str = Query("", description="Поиск по названию чата"),
    filter: str = Query("all", description="all | today | week | month"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
    chat_repo=Depends(get_chat_repository),
):
    """Список чатов пользователя (по умолчанию — последние 50)."""
    items = await chat_repo.list(user["id"], q, filter, limit, offset)
    total = await chat_repo.count(user["id"], q, filter)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: ChatCreate,
    user=Depends(get_current_user),
    chat_repo=Depends(get_chat_repository),
):
    """Создать новый чат."""
    title = (data.title or "Новый чат").strip() or "Новый чат"
    chat_id = await chat_repo.create(user["id"], title, data.agent_id)
    chat = await chat_repo.find_owned(chat_id, user["id"])
    return chat or {"id": chat_id, "title": title}


@router.get("/{chat_id}")
async def get_chat(
    chat_id: int,
    limit: int = Query(500, ge=1, le=2000),
    user=Depends(get_current_user),
    chat_repo=Depends(get_chat_repository),
    message_repo=Depends(get_message_repository),
):
    """Чат вместе с последними сообщениями."""
    chat = await chat_repo.find_owned(chat_id, user["id"])
    if not chat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Чат не найден")

    messages = await message_repo.list_by_chat(chat_id, limit)
    return {"chat": chat, "messages": messages}


@router.patch("/{chat_id}")
async def update_chat(
    chat_id: int,
    data: ChatUpdate,
    user=Depends(get_current_user),
    chat_repo=Depends(get_chat_repository),
):
    """Переименовать чат или сменить агента."""
    if not await chat_repo.is_owned(chat_id, user["id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Чат не найден")

    if data.title is not None:
        await chat_repo.rename(chat_id, user["id"], data.title.strip() or "Новый чат")

    if data.agent_id is not None:
        await chat_repo.set_agent(chat_id, user["id"], data.agent_id)

    chat = await chat_repo.find_owned(chat_id, user["id"])
    return chat or {"id": chat_id}


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    user=Depends(get_current_user),
    chat_repo=Depends(get_chat_repository),
    message_repo=Depends(get_message_repository),
):
    """Удалить чат и его сообщения."""
    if not await chat_repo.is_owned(chat_id, user["id"]):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Чат не найден")

    await message_repo.delete_by_chat(chat_id)
    await chat_repo.delete(chat_id, user["id"])
    return {"ok": True}


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: int,
    data: MessageCreate,
    user=Depends(get_current_user),
    chat_service=Depends(get_chat_service),
):
    """Отправить сообщение агенту и получить ответ."""
    if not await chat_service.chat_repo.is_owned(chat_id, user["id"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")

    return await chat_service.send(chat_id, data.content, user["id"])


@router.post("/{chat_id}/stream")
async def stream_message(
    chat_id: int,
    data: MessageCreate,
    user=Depends(get_current_user),
    chat_service=Depends(get_chat_service),
):
    """Отправить сообщение агенту со стримингом ответа (SSE)."""
    if not await chat_service.chat_repo.is_owned(chat_id, user["id"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")

    async def event_generator():
        try:
            async for event in chat_service.stream(chat_id, data.content, user["id"]):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as error:  # pragma: no cover - сетевые/провайдерские сбои
            payload = {"type": "error", "message": str(error)}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


__all__ = ["router"]
