# Техническое задание: BayLang AI

**Стек:** FastAPI (Cloudflare Workers / Docker) · Vue 3 · pydantic-ai · D1 / SQLite

---

## Содержание

1. [Общая информация](#1-общая-информация)
2. [Авторизация](#2-авторизация)
3. [Онлайн-чат](#3-онлайн-чат)
4. [Настройка провайдеров](#4-настройка-провайдеров)
5. [Настройка моделей](#5-настройка-моделей)
6. [Настройка агентов](#6-настройка-агентов)
7. [Итог](#7-итог)

---

## 1. Общая информация

### 1.1. Архитектура

Приложение состоит из двух частей:

- **Backend** — FastAPI, развёрнутый в Docker или на Cloudflare Workers. Контроллеры получают зависимости через `Depends` и собственный DI-контейнер (`container.register`, `container.singleton`, `container.get`).
- **Frontend** — Vue 3 в паттерне «страница + модель»: каждая страница лежит в своей папке (`src/pages/<Name>/NamePage.vue` + `src/pages/<Name>/NamePageModel.js`). Глобальная `AppLayoutModel` хранит модели всех страниц и управляется через `this.$layout`.

### 1.2. Требования к коду

- Использовать **Record-репозитории** для работы с БД — класс, инкапсулирующий SQL-запросы и методы доступа.
- На фронте бизнес-логика и state живут **только** в `*PageModel.js`, компонент отвечает за рендер и обработку событий.
- Для LLM-логики используется **pydantic-ai** с обязательной настройкой:
  ```python
  os.environ["PYDANTIC_AI_NO_BANNER"] = "1"
  ```

---

## 2. Авторизация

### 2.1. Описание

Пользователь входит в систему по паре **email + пароль**. При успешной авторизации выдаётся **JWT-токен** (access + refresh), который клиент хранит в `localStorage` и передаёт в заголовке `Authorization: Bearer <token>`. Авторизация разграничивает доступ к чатам и настройкам: каждый пользователь видит только свои данные.

### 2.2. Сценарии

1. **Регистрация** — пользователь указывает email, имя и пароль. Пароль хешируется (bcrypt). После регистрации выдаются токены и создаётся дефолтный провайдер OpenRouter.
2. **Вход** — проверка хеша пароля, выдача пары токенов.
3. **Обновление токена** — по `refresh_token` выдаётся новый `access_token` (TTL access — 30 мин, refresh — 7 дней).
4. **Выход** — refresh-токен инвалидируется (запись удаляется/помечается).

### 2.3. Схема базы данных

```sql
CREATE TABLE users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    email      TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    password   TEXT NOT NULL,          -- bcrypt hash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE refresh_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    token      TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    revoked    INTEGER DEFAULT 0
);
```

### 2.4. API

| Метод | URL              | Описание                        | Доступ   |
|-------|------------------|---------------------------------|----------|
| POST  | `/api/auth/register` | Регистрация                 | Public   |
| POST  | `/api/auth/login`    | Вход, выдача токенов        | Public   |
| POST  | `/api/auth/refresh`  | Обновление access-токена    | Public   |
| POST  | `/api/auth/logout`   | Инвалидация refresh-токена  | Auth     |
| GET   | `/api/auth/me`       | Текущий пользователь        | Auth     |

### 2.5. Репозиторий

```python
# src/core/repositories/user_repository.py

class UserRepository:
    """Record-репозиторий для работы с пользователями."""

    def __init__(self, database):
        self.database = database

    def create(self, email: str, name: str, password_hash: str) -> int:
        row = self.database.execute(
            """
            INSERT INTO users (email, name, password)
            VALUES (?, ?, ?)
            """,
            (email, name, password_hash),
        )
        return row.lastrowid

    def find_by_email(self, email: str) -> dict | None:
        return self.database.fetch_one(
            "SELECT * FROM users WHERE email = ?", (email,)
        )

    def find_by_id(self, user_id: int) -> dict | None:
        return self.database.fetch_one(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )

    def save_refresh_token(self, user_id: int, token: str, expires_at: str):
        self.database.execute(
            "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at),
        )

    def revoke_refresh_token(self, token: str):
        self.database.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE token = ?", (token,)
        )
```

### 2.6. Регистрация зависимостей и маршрутов

Файл src/core/auth.py
```python
@app.post("/api/auth/register")
async def register(data: RegisterSchema, user_repo=Depends(get_user_repository)):
    if user_repo.find_by_email(data.email):
        raise HTTPException(400, "Email already registered")

    password_hash = hash_password(data.password)
    user_id = user_repo.create(data.email, data.name, password_hash)
    tokens = issue_tokens(user_id)
    return {"user": {"id": user_id, "email": data.email}, **tokens}

@app.post("/api/auth/login")
async def login(data: LoginSchema, user_repo=Depends(get_user_repository)):
    user = user_repo.find_by_email(data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")

    tokens = issue_tokens(user["id"])
    return {"user": {"id": user["id"], "email": user["email"]}, **tokens}
```

```python
# src/core/app.py

def register_repositories():
    container.singleton(
        "user_repository",
        lambda c: UserRepository(c.get("database")),
    )

def register_routes():
    register_repositories()
    register_auth_routes()
```

### 2.7. JWT-зависимость для защищённых маршрутов

Добавить в файл
```python
# src/core/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo=Depends(get_user_repository),
) -> dict:
    payload = decode_token(credentials.credentials)  # raise 401 при ошибке
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    user = user_repo.find_by_id(payload["sub"])
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user
```

### 2.8. Frontend: страница входа

**Структура:** `src/pages/LoginPage/LoginPage.vue` + `src/pages/LoginPage/LoginPageModel.js`

```javascript
// src/pages/LoginPage/LoginPageModel.js
import LoginPage from "./LoginPage.vue";
import BasePageModel from "@/pages/BasePageModel";
import { api } from "@/services/api";

export class LoginPageModel extends BasePageModel
{
    state = {
        email: "",
        password: "",
        error: "",
        loading: false,
    };

    getComponent() { return LoginPage; }
    getTitle() { return "Вход"; }

    async submit()
    {
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await api.post("/api/auth/login", {
                email: this.state.email,
                password: this.state.password,
            });
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            this.$layout.getRouter().open("chats");
        } catch (e) {
            this.state.error = e.message || "Ошибка входа";
        } finally {
            this.state.loading = false;
        }
    }
}
```

```vue
<!-- src/pages/LoginPage/LoginPage.vue -->
<template>
    <div class="login">
        <h2>Вход</h2>
        <input v-model="model.state.email" placeholder="Email" />
        <input v-model="model.state.password" type="password" placeholder="Пароль" />
        <p v-if="model.state.error" class="error">{{ model.state.error }}</p>
        <button :disabled="model.state.loading" @click="model.submit()">Войти</button>
    </div>
</template>

<script>
export default {
    name: "LoginPage",
    computed: {
        model() { return this.$layout.getPage("LoginPageModel"); }
    }
}
</script>
```

### 2.9. API-клиент с автоматическим обновлением токена

```javascript
// services/ApiService.js

export class AuthApi extends ApiService {
    async request(method, url, body)
    {
        const headers = { "Content-Type": "application/json" };
        const token = localStorage.getItem("access_token");
        if (token) headers["Authorization"] = `Bearer ${token}`;

        let res = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined,
        });

        if (res.status === 401) {
            const refreshed = await this.refresh();
            if (refreshed) return this.request(method, url, body);
        }
        if (!res.ok) throw new Error((await res.json()).detail || "Request failed");
        return res.json();
    },

    get(url) { return this.request("GET", url); },
    post(url, body) { return this.request("POST", url, body); },
    put(url, body) { return this.request("PUT", url, body); },
    delete(url) { return this.request("DELETE", url); },
```

Добавить в AuthApi методы login, logout

```javascript
// services/AuthApi.js
export class AuthApi extends ApiService {
    async refresh()
    {
        const refresh = localStorage.getItem("refresh_token");
        if (!refresh) return false;
        const res = await fetch("/api/auth/refresh", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!res.ok) return false;
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        return true;
    }
};
```

---

## 3. Онлайн-чат

### 3.1. Описание

Основной экран приложения — чат с ИИ-агентом. Пользователь отправляет сообщение, бэкенд прогоняет его через **pydantic-ai агент** и возвращает ответ. История чатов хранится в БД с возможностью создания новых чатов, фильтрации и поиска. Список чатов — select list с последними **50 чатами**.

### 3.2. Схема базы данных

```sql
CREATE TABLE chats (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    agent_id   INTEGER REFERENCES agents(id),
    title      TEXT NOT NULL DEFAULT 'Новый чат',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id    INTEGER NOT NULL REFERENCES chats(id),
    role       TEXT NOT NULL,           -- 'user' | 'assistant'
    content    TEXT NOT NULL,
    context    TEXT,                    -- JSON: all_messages() из pydantic-ai
    usage      TEXT,                    -- JSON: токены/стоимость
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_chat ON messages(chat_id, created_at);
CREATE INDEX idx_chats_user ON chats(user_id, updated_at DESC);
```

> **Важно:** вместе с последним ответом агента сохраняется **полный контекст** (`result.all_messages()`), сериализованный через `ModelMessagesTypeAdapter`. Это позволяет продолжать диалог без потери истории инструментов.

### 3.3. API

| Метод | URL                          | Описание                                   | Доступ |
|-------|------------------------------|--------------------------------------------|--------|
| GET   | `/api/chats`                 | Список чатов (query: `q`, `limit=50`)      | Auth   |
| POST  | `/api/chats`                 | Создать чат (`agent_id`, `title`)          | Auth   |
| GET   | `/api/chats/{id}`            | Чат с последними N сообщениями             | Auth   |
| DELETE| `/api/chats/{id}`            | Удалить чат                                | Auth   |
| POST  | `/api/chats/{id}/messages`   | Отправить сообщение, получить ответ агента | Auth   |

### 3.4. Сервис чата (агент-цикл)

```python
# src/core/services/chat_service.py

import json
from pydantic_ai import ModelMessagesTypeAdapter, UsageLimits
from pydantic_core import to_jsonable_python


class ChatService:
    def __init__(self, chat_repo, message_repo, agent_factory):
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.agent_factory = agent_factory   # получает конфиг агента из БД

    async def send(self, chat_id: int, user_message: str) -> dict:
        chat = self.chat_repo.find_by_id(chat_id)

        # Восстанавливаем контекст из последнего сохранённого состояния
        last = self.message_repo.find_last_with_context(chat_id)
        context = (
            ModelMessagesTypeAdapter.validate_python(json.loads(last["context"]))
            if last else []
        )

        # Строим агента под этот чат (провайдер/модель/промпт из настроек)
        agent = self.agent_factory.build(chat["agent_id"])

        history = list(context)
        history.append(ModelRequest(parts=[UserPromptPart(content=user_message)]))

        result = await agent.run(
            user_message,
            message_history=context,
            usage_limits=UsageLimits(request_limit=None),
        )

        # Сохраняем ответ и полный контекст для следующего шага
        context_json = json.dumps(to_jsonable_python(result.all_messages()))
        msg_id = self.message_repo.create(
            chat_id=chat_id,
            role="assistant",
            content=result.output,
            context=context_json,
        )
        self.chat_repo.touch(chat_id, title=self._auto_title(chat, user_message))

        return {"id": msg_id, "role": "assistant", "content": result.output}

    @staticmethod
    def _auto_title(chat: dict, message: str) -> str | None:
        return message[:50] if chat["title"] == "Новый чат" else None
```

### 3.5. Маршрут чата

```python
# src/core/app.py

def get_chat_service():
    return container.get("chat_service")

@app.post("/api/chats/{chat_id}/messages")
async def send_message(
    chat_id: int,
    data: MessageSchema,
    user=Depends(get_current_user),
    chat_svc=Depends(get_chat_service),
):
    # Проверка владельца чата
    if not chat_svc.chat_repo.is_owned(chat_id, user["id"]):
        raise HTTPException(403, "Forbidden")
    return await chat_svc.send(chat_id, data.content)
```

### 3.6. Стриминг (рекомендуется)

Для живого ощущения «онлайн» ответ передаётся через **Server-Sent Events**:

```python
from fastapi.responses import StreamingResponse

@app.post("/api/chats/{chat_id}/stream")
async def stream_message(chat_id: int, data: MessageSchema, ...):
    async def gen():
        async with agent.run_stream(data.content, message_history=context) as result:
            async for chunk in result.stream_text(delta=True):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
```

На фронте — `EventSource` / `fetch` с reader:

```javascript
// src/pages/ChatPage/ChatPageModel.js
async send()
{
    const content = this.state.input;
    this.state.input = "";
    this.state.messages.push({ role: "user", content });
    this.state.typing = true;

    const res = await fetch(`/api/chats/${this.state.chatId}/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ content }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value);
        const lines = buffer.split("\n\n");
        buffer = lines.pop();
        for (const line of lines) {
            if (line.startsWith("data: ") && line !== "data: [DONE]") {
                const chunk = JSON.parse(line.slice(6));
                this.appendToLastMessage(chunk.text);   // живое обновление UI
            }
        }
    }
    this.state.typing = false;
}
```

### 3.7. Интерфейс истории чатов

Компонент истории содержит:
- **Select list** последних 50 чатов;
- **Поиск** по названию (query `q` к `/api/chats`);
- **Фильтр** по дате создания/агента;
- Кнопку «Новый чат».

```javascript
// src/pages/HistoryPage/HistoryPageModel.js
state = {
    chats: [],
    total: 0,
    query: "",
    filter: "all",   // 'all' | 'today' | 'week'
    limit: 50,
    offset: 0,
};

async init()
{
    await this.load();
}

async load()
{
    const params = new URLSearchParams({
        q: this.state.query,
        filter: this.state.filter,
        limit: this.state.limit,
        offset: this.state.offset,
    });
    const data = await api.get(`/api/chats?${params}`);
    this.state.chats = data.items;
    this.state.total = data.total;
}

async createChat()
{
    const chat = await api.post("/api/chats", { title: "Новый чат" });
    this.$layout.getRouter().open("chat", { id: chat.id });
}
```

```vue
<!-- src/pages/HistoryPage/HistoryPage.vue -->
<template>
    <div class="history">
        <input v-model="model.state.query"
               placeholder="Поиск по чатам..."
               @input="model.debouncedLoad()" />
        <select v-model="model.state.filter" @change="model.load()">
            <option value="all">Все</option>
            <option value="today">Сегодня</option>
            <option value="week">Неделя</option>
        </select>
        <button @click="model.createChat()">＋ Новый чат</button>

        <ul class="chat-list">
            <li v-for="chat in model.state.chats" :key="chat.id"
                @click="$layout.getRouter().open('chat', { id: chat.id })">
                <span class="title">{{ chat.title }}</span>
                <span class="date">{{ chat.updated_at }}</span>
            </li>
        </ul>
    </div>
</template>
```

---

## 4. Настройка провайдеров

### 4.1. Описание

Провайдер — это подключённый LLM-сервис (OpenRouter, OpenAI, Anthropic и т.д.). Поля: **название, URL, API key**. Провайдер по умолчанию — **OpenRouter**, у которого дополнительно поддерживается **список провайдеров через запятую** (параметр `only`, фильтрующий, какие upstream-провайдеры использовать).

### 4.2. Схема базы данных

```sql
CREATE TABLE providers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    name       TEXT NOT NULL,               -- 'OpenRouter'
    url        TEXT NOT NULL DEFAULT 'https://openrouter.ai/api/v1',
    api_key    TEXT NOT NULL,
    extra      TEXT,                        -- JSON: {"only": ["anthropic", "openai"]}
    is_default INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3. API

| Метод | URL                   | Описание                        | Доступ |
|-------|-----------------------|---------------------------------|--------|
| GET   | `/api/providers`      | Список провайдеров              | Auth   |
| POST  | `/api/providers`      | Создать провайдер               | Auth   |
| PUT   | `/api/providers/{id}` | Редактировать                   | Auth   |
| DELETE| `/api/providers/{id}` | Удалить                         | Auth   |

### 4.4. Схемы данных (pydantic)

```python
# src/core/schemas/provider.py
from pydantic import BaseModel, Field

class ProviderCreate(BaseModel):
    name: str
    url: str = "https://openrouter.ai/api/v1"
    api_key: str
    only: list[str] = Field(default_factory=list)   # список через запятую
    is_default: bool = False

class ProviderOut(BaseModel):
    id: int
    name: str
    url: str
    only: list[str]
    is_default: bool
```

### 4.5. Пример кода для OpenRouter

При сохранении поля `only` конвертируется из строки через запятую в список:

```python
# src/core/provider_service.py

def build_openrouter_config(provider_row: dict) -> OpenRouterProviderConfig:
    config = OpenRouterProviderConfig()
    raw = provider_row.get("extra") or "{}"
    extra = json.loads(raw)

    if extra.get("only"):
        items = extra["only"].split(",") if isinstance(extra["only"], str) else extra["only"]
        config["only"] = [s.strip() for s in items if s.strip()]

    return config
```

```python
# Пример создания провайдера в API
@app.post("/api/providers")
async def create_provider(
    data: ProviderCreate,
    user=Depends(get_current_user),
    provider_repo=Depends(get_provider_repository),
):
    extra = json.dumps({"only": ",".join(data.only)})
    provider_id = provider_repo.create(
        user_id=user["id"],
        name=data.name,
        url=data.url,
        api_key=data.api_key,
        extra=extra,
        is_default=data.is_default,
    )
    return {"id": provider_id}
```

### 4.6. Инициализация провайдера по умолчанию

При регистрации пользователя автоматически создаётся запись OpenRouter:

```python
def create_default_provider(user_repo, provider_repo, user_id: int):
    provider_repo.create(
        user_id=user_id,
        name="OpenRouter",
        url="https://openrouter.ai/api/v1",
        api_key="",  # пользователь заполняет сам
        extra=json.dumps({"only": []}),
        is_default=1,
    )
```

---

## 5. Настройка моделей

### 5.1. Описание

Модель — это связка «название LLM-модели + провайдер + параметры генерации» (температура, max_tokens и т.п.). Модель выбирается в настройках агента.

### 5.2. Схема базы данных

```sql
CREATE TABLE models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    name        TEXT NOT NULL,              -- 'anthropic/claude-3.5-sonnet'
    temperature REAL DEFAULT 0.7,
    max_tokens  INTEGER,
    extra       TEXT,                       -- JSON: прочие параметры (top_p и т.п.)
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3. API

| Метод | URL               | Описание                    | Доступ |
|-------|-------------------|-----------------------------|--------|
| GET   | `/api/models`     | Список моделей              | Auth   |
| POST  | `/api/models`     | Создать модель              | Auth   |
| PUT   | `/api/models/{id}`| Редактировать               | Auth   |
| DELETE| `/api/models/{id}`| Удалить                     | Auth   |

### 5.4. Пример кода

```python
# src/core/schemas/model.py
class ModelCreate(BaseModel):
    provider_id: int
    name: str = Field(..., examples=["anthropic/claude-3.5-sonnet"])
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None

class ModelOut(BaseModel):
    id: int
    provider_id: int
    name: str
    temperature: float
    max_tokens: int | None
```

```python
# Пример использования в фабрике агентов
def build_openrouter_model(model_row: dict, provider_row: dict):
    config = build_openrouter_config(provider_row)

    settings = OpenRouterModelSettings(
        openrouter_cache_instructions=True,
        openrouter_cache_messages=True,
        openrouter_cache_tool_definitions=True,
        openrouter_provider=config,
    )
    if model_row.get("temperature") is not None:
        settings["temperature"] = model_row["temperature"]
    if model_row.get("max_tokens"):
        settings["max_tokens"] = model_row["max_tokens"]

    return OpenRouterModel(
        model_row["name"],
        provider=OpenRouterProvider(
            api_key=provider_row["api_key"],
            app_url=APP_URL,
            app_title=APP_TITLE,
        ),
        settings=settings,
    )
```

---

## 6. Настройка агентов

### 6.1. Описание

Агент — это «персона» бота: **системный промпт** + выбранная **модель**. Чат ссылается на агента. Агенты создаются/редактируются на отдельной странице настроек.

### 6.2. Схема базы данных

```sql
CREATE TABLE agents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    name          TEXT NOT NULL,               -- 'Помощник'
    system_prompt TEXT NOT NULL DEFAULT '',
    model_id      INTEGER REFERENCES models(id),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.3. API

| Метод | URL                | Описание                          | Доступ |
|-------|--------------------|-----------------------------------|--------|
| GET   | `/api/agents`      | Список агентов                    | Auth   |
| POST  | `/api/agents`      | Создать агента                    | Auth   |
| PUT   | `/api/agents/{id}` | Редактировать                     | Auth   |
| DELETE| `/api/agents/{id}` | Удалить                           | Auth   |

### 6.4. Фабрика агентов (pydantic-ai)

```python
# src/core/services/agent_factory.py
import os
os.environ["PYDANTIC_AI_NO_BANNER"] = "1"

from pydantic_ai import Agent

APP_URL = "https://baylang.com/"
APP_TITLE = "BayLang AI"


class AgentFactory:
    def __init__(self, agent_repo, model_repo, provider_repo):
        self.agent_repo = agent_repo
        self.model_repo = model_repo
        self.provider_repo = provider_repo

    def build(self, agent_id: int) -> Agent:
        agent_row = self.agent_repo.find_by_id(agent_id)
        model_row = self.model_repo.find_by_id(agent_row["model_id"])
        provider_row = self.provider_repo.find_by_id(model_row["provider_id"])

        model = build_openrouter_model(model_row, provider_row)

        agent = Agent(
            model,
            system_prompt=agent_row["system_prompt"] or "Ты — полезный ассистент.",
            retries=10,
        )
        return agent
```

### 6.5. Регистрация в DI-контейнере

```python
# src/core/app.py

def register_services():
    container.singleton(
        "agent_factory",
        lambda c: AgentFactory(
            c.get("agent_repository"),
            c.get("model_repository"),
            c.get("provider_repository"),
        ),
    )
    container.singleton(
        "chat_service",
        lambda c: ChatService(
            c.get("chat_repository"),
            c.get("message_repository"),
            c.get("agent_factory"),
        ),
    )

def create_app():
    container.singleton("database", lambda c: SqliteDatabase())
    container.singleton("env", lambda c: Env(os.environ))
    register_repositories()
    register_services()
    register_routes()
    register_static()
    return container.get("app")
```

### 6.6. Frontend: страница настроек

**Структура:** `src/pages/SettingsPage/SettingsPage.vue` + `SettingsPageModel.js`

```javascript
// src/pages/SettingsPage/SettingsPageModel.js
import SettingsPage from "./SettingsPage.vue";
import BasePageModel from "@/pages/BasePageModel";
import { api } from "@/services/api";

export class SettingsPageModel extends BasePageModel
{
    state = {
        tab: "providers",        // 'providers' | 'models' | 'agents'
        providers: [],
        models: [],
        agents: [],

        // Формы
        providerForm: { name: "OpenRouter", url: "https://openrouter.ai/api/v1", api_key: "", only: "" },
        modelForm: { provider_id: null, name: "", temperature: 0.7, max_tokens: null },
        agentForm: { name: "", system_prompt: "", model_id: null },
    };

    getComponent() { return SettingsPage; }
    getTitle() { return "Настройки"; }

    async init()
    {
        await this.loadAll();
    }

    async loadAll()
    {
        const [providers, models, agents] = await Promise.all([
            api.get("/api/providers"),
            api.get("/api/models"),
            api.get("/api/agents"),
        ]);
        this.state.providers = providers;
        this.state.models = models;
        this.state.agents = agents;
    }

    async saveProvider()
    {
        // Список провайдеров OpenRouter вводим через запятую
        const only = this.state.providerForm.only
            .split(",")
            .map(s => s.trim())
            .filter(Boolean);

        await api.post("/api/providers", { ...this.state.providerForm, only });
        await this.loadAll();
    }

    async saveModel()
    {
        await api.post("/api/models", this.state.modelForm);
        await this.loadAll();
    }

    async saveAgent()
    {
        await api.post("/api/agents", this.state.agentForm);
        await this.loadAll();
    }
}
```

```vue
<!-- src/pages/SettingsPage/SettingsPage.vue -->
<template>
    <div class="settings">
        <nav class="tabs">
            <button :class="{ active: model.state.tab === 'providers' }"
                    @click="model.state.tab = 'providers'">Провайдеры</button>
            <button :class="{ active: model.state.tab === 'models' }"
                    @click="model.state.tab = 'models'">Модели</button>
            <button :class="{ active: model.state.tab === 'agents' }"
                    @click="model.state.tab = 'agents'">Агенты</button>
        </nav>

        <!-- Провайдеры -->
        <section v-if="model.state.tab === 'providers'">
            <input v-model="model.state.providerForm.name" placeholder="Название" />
            <input v-model="model.state.providerForm.url" placeholder="URL" />
            <input v-model="model.state.providerForm.api_key" type="password" placeholder="API Key" />
            <input v-model="model.state.providerForm.only"
                   placeholder="Провайдеры через запятую (например: anthropic, openai)" />
            <button @click="model.saveProvider()">Сохранить</button>

            <ul>
                <li v-for="p in model.state.providers" :key="p.id">
                    <strong>{{ p.name }}</strong> — {{ p.url }}
                    <em v-if="p.only.length">[{{ p.only.join(", ") }}]</em>
                </li>
            </ul>
        </section>

        <!-- Модели -->
        <section v-if="model.state.tab === 'models'">
            <select v-model="model.state.modelForm.provider_id">
                <option v-for="p in model.state.providers" :value="p.id">{{ p.name }}</option>
            </select>
            <input v-model="model.state.modelForm.name" placeholder="Название модели" />
            <input v-model.number="model.state.modelForm.temperature" type="number" step="0.1" min="0" max="2" />
            <button @click="model.saveModel()">Сохранить</button>
        </section>

        <!-- Агенты -->
        <section v-if="model.state.tab === 'agents'">
            <input v-model="model.state.agentForm.name" placeholder="Имя агента" />
            <select v-model="model.state.agentForm.model_id">
                <option v-for="m in model.state.models" :value="m.id">{{ m.name }}</option>
            </select>
            <textarea v-model="model.state.agentForm.system_prompt"
                      placeholder="Системный промпт..."></textarea>
            <button @click="model.saveAgent()">Сохранить</button>
        </section>
    </div>
</template>

<script>
export default {
    name: "SettingsPage",
    computed: {
        model() { return this.$layout.getPage("SettingsPageModel"); }
    }
}
</script>
```

---

## 7. Итог

В данном техническом задании описана полная функциональность **BayLang AI** по пяти ключевым модулям:

- **Авторизация** реализована на JWT (access + refresh) с bcrypt-хешированием паролей, защищёнными маршрутами через `Depends(get_current_user)` и автоматическим обновлением токена на фронте — это надёжная и стандартная база для разграничения доступа.

- **Онлайн-чат** построен вокруг pydantic-ai: сервис чата восстанавливает контекст из сохранённого `all_messages()`, прогоняет запрос через агента и сохраняет полный контекст в JSON, что гарантирует непрерывность диалога. Стриминг через SSE делает общение живым, а история с поиском и фильтром по последним 50 чатам — удобной.

- **Провайдеры** хранят название, URL и API-ключ, а для OpenRouter дополнительно поддерживается список upstream-провайдеров через запятую (параметр `only`), который напрямую маппится в `OpenRouterProviderConfig`.

- **Модели** связывают провайдер с названием LLM-модели и параметрами генерации (температура, max_tokens), которые применяются через `OpenRouterModelSettings` при сборке модели.

- **Агенты** — это системный промпт + выбранная модель; фабрика агентов собирает всё вместе и регистрируется в DI-контейнере, что полностью соответствует архитектуре проекта (FastAPI + container + Record-репозитории + паттерн «страница + модель» на Vue).

**Вывод:** задание структурировано так, что каждый модуль можно реализовать независимо, при этом они связаны через единый DI-контейнер и типизированные pydantic-схемы. Разработка может идти параллельно по фронтенду и бэкенду, а примеры кода дают готовую отправную точку для каждой функциональности. 🚀