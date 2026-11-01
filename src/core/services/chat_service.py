"""Сервис чата: агент-цикл pydantic-ai + сохранение контекста."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import HTTPException, status


class ChatService:
    """Отправляет сообщения агенту и сохраняет историю вместе с контекстом."""

    def __init__(self, chat_repo, message_repo, agent_factory) -> None:
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.agent_factory = agent_factory

    # ------------------------------------------------------------------
    # Отправка сообщения (обычный режим)
    # ------------------------------------------------------------------
    async def send(self, chat_id: int, user_message: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Прогнать сообщение через агента и вернуть ответ."""
        from pydantic_ai import UsageLimits
        from pydantic_core import to_jsonable_python

        chat = await self._get_chat(chat_id, user_id)
        context = await self.load_context(chat_id)
        agent = await self._build_agent(chat, user_id)

        await self.message_repo.create(chat_id=chat_id, role="user", content=user_message)

        result = await agent.run(
            user_message,
            message_history=context,
            usage_limits=UsageLimits(request_limit=None),
        )

        output = str(result.output)
        context_json = json.dumps(to_jsonable_python(result.all_messages()), ensure_ascii=False)
        usage_json = json.dumps(to_jsonable_python(result.usage()), ensure_ascii=False)

        message_id = await self.message_repo.create(
            chat_id=chat_id,
            role="assistant",
            content=output,
            context=context_json,
            usage=usage_json,
        )
        await self.chat_repo.touch(chat_id, title=self._auto_title(chat, user_message))

        return {
            "id": message_id,
            "chat_id": chat_id,
            "role": "assistant",
            "content": output,
            "usage": to_jsonable_python(result.usage()),
        }

    # ------------------------------------------------------------------
    # Стриминг (SSE)
    # ------------------------------------------------------------------
    async def stream(
        self,
        chat_id: int,
        user_message: str,
        user_id: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Отправить сообщение и отдавать ответ частями (SSE)."""
        from pydantic_ai import UsageLimits
        from pydantic_core import to_jsonable_python

        chat = await self._get_chat(chat_id, user_id)
        context = await self.load_context(chat_id)
        agent = await self._build_agent(chat, user_id)

        await self.message_repo.create(chat_id=chat_id, role="user", content=user_message)

        chunks: List[str] = []
        all_messages: List[Any] = []

        async with agent.run_stream(
            user_message,
            message_history=context,
            usage_limits=UsageLimits(request_limit=None),
        ) as result:
            async for delta in result.stream_text(delta=True):
                if not delta:
                    continue
                chunks.append(delta)
                yield {"type": "delta", "text": delta}

            try:
                all_messages = list(result.all_messages())
            except Exception:  # pragma: no cover - зависит от версии pydantic-ai
                all_messages = []

        output = "".join(chunks)

        if not all_messages:
            all_messages = await self._fallback_messages(context, user_message, output)

        context_json = json.dumps(to_jsonable_python(all_messages), ensure_ascii=False)
        message_id = await self.message_repo.create(
            chat_id=chat_id,
            role="assistant",
            content=output,
            context=context_json,
        )
        await self.chat_repo.touch(chat_id, title=self._auto_title(chat, user_message))

        yield {
            "type": "done",
            "message": {
                "id": message_id,
                "chat_id": chat_id,
                "role": "assistant",
                "content": output,
            },
        }

    # ------------------------------------------------------------------
    # Контекст
    # ------------------------------------------------------------------
    async def load_context(self, chat_id: int) -> List[Any]:
        """Восстановить контекст pydantic-ai из сохранённого сообщения."""
        from pydantic_ai import ModelMessagesTypeAdapter

        last = await self.message_repo.find_last_with_context(chat_id)
        if not last or not last.get("context"):
            return []

        try:
            payload = json.loads(last["context"])
            return list(ModelMessagesTypeAdapter.validate_python(payload))
        except Exception:  # pragma: no cover - повреждённый контекст
            return []

    async def _fallback_messages(self, context: List[Any], user_message: str, output: str) -> List[Any]:
        """Собрать историю вручную, если `all_messages()` недоступен."""
        from pydantic_ai import ModelRequest, ModelResponse, TextPart, UserPromptPart

        messages = list(context)
        messages.append(ModelRequest(parts=[UserPromptPart(content=user_message)]))
        messages.append(ModelResponse(parts=[TextPart(content=output)]))
        return messages

    # ------------------------------------------------------------------
    # Вспомогательное
    # ------------------------------------------------------------------
    async def _get_chat(self, chat_id: int, user_id: Optional[int]) -> Dict[str, Any]:
        """Загрузить чат и проверить права доступа."""
        if user_id is None:
            chat = await self.chat_repo.find_by_id(chat_id)
        else:
            chat = await self.chat_repo.find_owned(chat_id, user_id)

        if not chat:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Чат не найден")
        return chat

    async def _build_agent(self, chat: Dict[str, Any], user_id: Optional[int]) -> Any:
        """Собрать агента для чата."""
        from core.services.agent_factory import AgentError

        try:
            return await self.agent_factory.build(chat.get("agent_id"), user_id)
        except AgentError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error

    @staticmethod
    def _auto_title(chat: Dict[str, Any], message: str) -> Optional[str]:
        """Заголовок по умолчанию заменяется первым сообщением пользователя."""
        if (chat.get("title") or "") == "Новый чат":
            return (message or "").strip()[:50]
        return None


__all__ = ["ChatService"]
