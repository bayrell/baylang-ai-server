# AGENTS.md — BayLang AI

Руководство для ИИ-агентов и новых разработчиков, работающих в этом репозитории.
Документ описывает **фактическое** состояние кода: все пути, команды и правила сверены с
исходниками. Расхождения между документацией и кодом вынесены в раздел
[«Известные проблемы»](#известные-проблемы-и-расхождения).

---

## 1. О проекте

**BayLang AI** — веб-приложение для общения с ИИ-агентами: чаты с сохранённой историей,
настройка провайдеров, моделей и «персон» (агентов).

| Слой       | Технологии                                                        |
|------------|-------------------------------------------------------------------|
| Backend    | Python ≥ 3.12, FastAPI, pydantic-ai, PyJWT, bcrypt, SQLite / Cloudflare D1 |
| Frontend   | Vue 3 (без роутера и UI-кита), Vite 6, собственный History-API роутер |
| Инфраструктура | Docker (многостадийная сборка), Cloudflare Workers (`python_workers`) |

Три ключевые сущности домена, связанные по цепочке:

```
провайдер (url + api_key + список upstream `only`)
   └── модель (имя LLM + temperature + max_tokens)
          └── агент (системный промпт + выбранная модель)
                 └── чат (агент + сообщения + сохранённый контекст pydantic-ai)
```

---

## 2. Структура репозитория

```
.
├── AGENTS.md                 ← этот файл
├── README.md                 ← пользовательская документация
├── LICENSE
├── build.sh                  ← единая точка сборки/запуска (см. §7)
├── Dockerfile                ← многостадийная сборка: node:22-alpine → python:3.12-slim
├── .dockerignore
├── docs/
│   ├── about.md              ← референсы по pydantic-ai из исходного ТЗ
│   ├── architecture.md       ← исходные требования к DI-контейнеру и фронтенду
│   └── task_v1.md            ← полное ТЗ (37 КБ)
└── src/                      ← корень проекта: backend И frontend одновременно
    ├── app.py                ← точка входа для Docker (uvicorn app:create_app --factory)
    ├── main.py               ← точка входа для Cloudflare Workers (WorkerEntrypoint)
    ├── requirements.txt      ← runtime-зависимости backend
    ├── pyproject.toml        ← метаданные + dev-группа (pytest, httpx, workers-py)
    │
    ├── core/                 ← ядро backend
    │   ├── app.py            ← сборка FastAPI: репозитории → сервисы → маршруты → статика
    │   ├── app_meta.py       ← APP_TITLE / APP_VERSION / APP_DESCRIPTION
    │   ├── config.py         ← класс Env: доступ к os.environ И bindings Workers
    │   ├── container.py      ← DI-контейнер (register / singleton / instance / get)
    │   ├── dependencies.py   ← Depends-обёртки над контейнером + get_current_user
    │   ├── auth.py           ← регистрация / вход / refresh / logout / me
    │   ├── security.py       ← bcrypt + JWT (HS256)
    │   ├── database/
    │   │   ├── base.py       ← абстракция Database + ExecuteResult
    │   │   ├── sqlite.py     ← реализация поверх sqlite3 (autocommit, RLock)
    │   │   ├── d1.py         ← реализация поверх Cloudflare D1 (binding "DB")
    │   │   └── migrations.py ← единственный список DDL (одинаков для SQLite и D1)
    │   ├── repositories/     ← Record-репозитории (сырой SQL внутри)
    │   │   ├── base.py, user_repository.py, provider_repository.py,
    │   │   ├── model_repository.py, agent_repository.py,
    │   │   └── chat_repository.py, message_repository.py
    │   ├── schemas/          ← pydantic-схемы запросов/ответов
    │   │   └── auth.py, provider.py, model.py, agent.py, chat.py
    │   ├── services/         ← бизнес-логика
    │   │   ├── chat_service.py     ← агент-цикл + SSE + сохранение контекста
    │   │   ├── agent_factory.py    ← сборка агента из БД
    │   │   ├── model_service.py    ← сборка LLM-модели pydantic-ai
    │   │   └── provider_service.py ← работа с полем `only` и default-провайдером
    │   └── routes/           ← API-маршруты (префикс /api)
    │       ├── system.py, chats.py, providers.py, models.py, agents.py
    │
    ├── pages/                ← frontend: страницы + глобальная модель
    │   ├── App.vue           ← корневой компонент (рендерит AppLayout)
    │   ├── AppLayout.vue     ← шапка, навигация, контейнер страницы
    │   ├── AppLayoutModel.js ← глобальная модель: роутер + все модели страниц
    │   ├── Router.js         ← собственный роутер (url ↔ route ↔ модель)
    │   ├── BasePageModel.js  ← базовый класс модели страницы
    │   ├── IndexPage/  LoginPage/  RegisterPage/
    │   ├── HistoryPage/       ← история чатов: поиск, фильтр, select-list
    │   ├── ChatPage/          ← чат с агентом + чтение SSE-потока
    │   └── SettingsPage/      ← вкладки: провайдеры / модели / агенты
    │
    ├── services/             ← HTTP-клиент frontend
    │   ├── ApiService.js     ← fetch-обёртка, Bearer-заголовок, авто-refresh при 401
    │   ├── AuthApi.js        ← login / register / logout / me + refresh()
    │   └── api.js            ← единый экземпляр `api` (AuthApi) для всех страниц
    │
    ├── assets/main.css       ← глобальные стили и CSS-переменные темы
    ├── index.html            ← HTML-точка входа Vite
    ├── main.js               ← JS-точка входа: создаёт layout, монтирует Vue
    ├── package.json          ← frontend-зависимости (vue, vite, @vitejs/plugin-vue)
    ├── vite.config.js        ← alias "@", outDir, dev-прокси /api → :8000
    └── wrangler.jsonc        ← конфигурация Cloudflare Workers + binding D1 "DB"
```

> **Важно:** `src/` совмещает в себе backend и frontend. Python-код импортируется как
> пакет `core` — поэтому `sys.path` должен содержать `src/` (это делают `src/app.py`
> и `src/main.py` через `sys.path.insert`).

---

## 3. Архитектура backend

### 3.1 DI-контейнер

`core/container.py` — минимальный контейнер без внешних зависимостей:

| Метод                         | Поведение                                                        |
|-------------------------------|------------------------------------------------------------------|
| `register(name, factory)`     | transient — новый объект при каждом `get()`                       |
| `singleton(name, factory)`    | создаётся один раз и кэшируется                                 |
| `instance(name, value)`       | готовый объект (для тестов и моков)                              |
| `get(name)`                   | достаёт или создаёт зависимость; `KeyError` если не зарегистрирована |
| `has(name)` / `reset()`       | проверка регистрации / полный сброс (используется в тестах)       |

Фабрика может принимать контейнер или не принимать аргументов — вызов разбирается
автоматически по сигнатуре (`inspect.signature`):

```python
container.singleton("database", lambda c: SqliteDatabase(c.get("env").get("DATABASE_PATH")))
container.singleton("app", lambda: FastAPI(...))   # без аргументов — тоже валидно
```

### 3.2 Правило слоёв

Строгое направление зависимостей, нарушать нельзя:

```
routes  →  services  →  repositories  →  database  →  SQL
   ↓            ↓            ↓
schemas   dependencies   (DI-контейнер)
```

- **Маршрут** (`core/routes/*`) не содержит SQL и не знает про БД. Он получает
  зависимости через `Depends(...)` и вызывает сервис или репозиторий.
- **Сервис** (`core/services/*`) содержит бизнес-логику и не пишет SQL.
- **Репозиторий** (`core/repositories/*`) — Record-паттерн: SQL лежит только здесь,
  наружу отдаёт `dict`-строки.
- **Схемы** (`core/schemas/*`) — pydantic-модели для валидации тела запроса и формы ответа.

Все зависимости регистрируются в `core/app.py`:
`register_repositories()` → `register_services()` → `register_routes()`.

### 3.3 Доступ к данным

Абстракция `Database` (`core/database/base.py`) с тремя методами:
`execute`, `fetch_one`, `fetch_all` (+ `execute_many` по умолчанию).
Две реализации:

- `SqliteDatabase` — `sqlite3` с `isolation_level=None` (autocommit), `PRAGMA foreign_keys = ON`,
  `check_same_thread=False`, защита через `threading.RLock`, одно соединение на процесс.
- `D1Database` — Cloudflare D1, binding **`DB`** (имя в `wrangler.jsonc` должно совпадать).

Обе платформы понимают базовый диалект SQLite, поэтому **список DDL один** —
`core/database/migrations.py`. Миграции идемпотентны (`CREATE TABLE/INDEX IF NOT EXISTS`)
и накатываются:

- в Docker — в `lifespan` (`await database.initialize()`);
- в Workers — лениво при первом запросе (`Default._ensure_schema` в `src/main.py`).

Схема БД (7 таблиц):

| Таблица          | Ключевые поля                                                                     |
|------------------|-----------------------------------------------------------------------------------|
| `users`          | `id, email (UNIQUE), name, password, created_at`                                   |
| `refresh_tokens` | `id, user_id, token (UNIQUE), expires_at, revoked, created_at`                    |
| `providers`      | `id, user_id, name, url, api_key, extra (JSON), is_default, created_at`            |
| `models`         | `id, user_id, provider_id, name, temperature, max_tokens, extra (JSON), created_at` |
| `agents`         | `id, user_id, name, system_prompt, model_id, created_at`                          |
| `chats`          | `id, user_id, agent_id, title, created_at, updated_at`                            |
| `messages`       | `id, chat_id, role, content, context (JSON), usage (JSON), created_at`             |

Колонки `extra` в `providers` и `models` — **JSON-строка**. Поля `only` (список
upstream-провайдеров OpenRouter) и любые дополнительные параметры генерации хранятся там
и разбираются в `core/services/provider_service.py` / `model_service.py`.

### 3.4 Авторизация

- Пароли — **bcrypt** (`security.hash_password`), вход короче 72 байт обрезается.
- Access-токен — **JWT HS256**, payload: `sub` (user_id), `type="access"`, `iat`, `exp`, `jti`.
- Refresh-токен — **непрозрачный** `secrets.token_urlsafe(48)`, хранится в БД,
  поэтому его можно отозвать (`revoked = 1`).
- Защита маршрутов — `Depends(get_current_user)` (`core/dependencies.py`):
  проверяется Bearer-заголовок, тип токена и существование пользователя.
- Frontend хранит токены в `localStorage` (`access_token`, `refresh_token`, `user`)
  и при 401 автоматически обновляет access-токен и повторяет запрос
  (`ApiService.request` → `AuthApi.refresh`).

### 3.5 Чат и pydantic-ai

`core/services/chat_service.py` — центральная часть:

1. Проверяет владение чатом (`find_owned`) — доступ разграничен по `user_id`.
2. Восстанавливает контекст: `message_repo.find_last_with_context()` →
   `json.loads` → `ModelMessagesTypeAdapter.validate_python()`.
3. Собирает агента через `AgentFactory`.
4. Сохраняет сообщение пользователя, запускает `agent.run(...)` или `agent.run_stream(...)`.
5. Сохраняет ответ ассистента вместе с **полным контекстом** (`result.all_messages()`)
   и `usage`, сериализованными через `pydantic_core.to_jsonable_python`.
6. Обновляет `chats.updated_at`; если заголовок ещё «Новый чат» — подставляет первые
   50 символов сообщения пользователя.

Стриминг — SSE: `core/routes/chats.py` отдаёт `StreamingResponse` с
`media_type="text/event-stream"` и заголовками `Cache-Control: no-cache`,
`Connection: keep-alive`, `X-Accel-Buffering: no`. События: `delta` → `done` → `error`,
в конце — служебный кадр `data: [DONE]`.

### 3.6 Сборка модели по провайдеру

`core/services/model_service.py::build_model` выбирает реализацию по типу провайдера
(`provider_service.is_openrouter` — по имени «OpenRouter» или наличию `openrouter.ai` в URL):

- **OpenRouter** → `OpenRouterModel` + `OpenRouterProvider(api_key, app_url, app_title)`,
  настройки через `OpenRouterModelSettings` (включаются кеши OpenRouter и
  `openrouter_provider={"only": [...]}` из поля `only`).
- **Любой OpenAI-совместимый** → `OpenAIChatModel` + `OpenAIProvider(api_key, base_url)`.

`AgentFactory` собирает `Agent(model, system_prompt=..., retries=10)`. Если у агента не
выбрана модель или не найден провайдер — бросается `AgentError`, который
`ChatService` превращает в `HTTP 400`.

---

## 4. Архитектура frontend

### 4.1 Паттерн «страница + модель»

Обязательное правило проекта: **одна страница = одна папка с двумя файлами**.

```
pages/ChatPage/
├── ChatPage.vue        ← только рендер + обработчики событий
└── ChatPageModel.js   ← состояние, данные, бизнес-логика
```

- `ChatPageModel extends BasePageModel` (`pages/BasePageModel.js`):
  - поле `state` — реактивное состояние страницы;
  - `getComponent()` — возвращает `.vue`-компонент;
  - `getTitle()` — заголовок;
  - `init(params)` — загрузка данных (вызывается роутером при открытии);
  - `navigate(name, params)` — переход на другую страницу.
- В `.vue` данные берутся из `this.$layout.getPage("<Name>Model")`, глобальная модель
  доступна как `this.$layout` (через `app.config.globalProperties`).

### 4.2 Роутер

`pages/Router.js` — собственный роутер без внешних зависимостей:

| Метод                | Назначение                                                     |
|----------------------|-----------------------------------------------------------------|
| `add(name, url, ModelClass, options)` | регистрация маршрута; `options.auth = true` → требует авторизации |
| `url(name, params)`  | построение url с подстановкой `:param`                          |
| `find(url)`          | поиск маршрута по url, возвращает `{ name, params, route }`      |
| `open(name, params)` / `openUrl(url)` | переход с `history.pushState`                  |
| `show(name, params)` | показ страницы без изменения истории, вызывает `model.init()`    |
| `init()`             | обработчик `popstate` + открытие текущей страницы               |
| `getCurrentPage()`   | имя текущей страницы                                            |
| `getPage(name)`      | модель страницы                                                 |

`AppLayoutModel` (`pages/AppLayoutModel.js`) владеет роутером и регистрирует маршруты:

| name       | url         | модель            | auth |
|------------|-------------|-------------------|------|
| `index`    | `/`         | `IndexPageModel`  | нет  |
| `login`    | `/login`    | `LoginPageModel`  | нет  |
| `register` | `/register` | `RegisterPageModel`| нет  |
| `chats`    | `/chats`    | `HistoryPageModel`| да   |
| `chat`     | `/chat/:id` | `ChatPageModel`   | да   |
| `settings` | `/settings` | `SettingsPageModel`| да  |

### 4.3 HTTP-клиент

- `services/ApiService.js` — базовый клиент: JSON, заголовок `Authorization: Bearer …`,
  разбор `detail` из тела ошибки, повтор запроса после успешного refresh при 401.
- `services/AuthApi.js` — наследник: `login`, `register`, `logout`, `me`, `refresh`,
  `saveTokens` / `clearTokens`.

---

## 5. API

Все маршруты под префиксом `/api`. «Auth» — требует `Authorization: Bearer <access_token>`.

| Метод   | URL                        | Описание                                             | Доступ |
|---------|----------------------------|------------------------------------------------------|--------|
| GET     | `/api/health`              | Health-check (используется в HEALTHCHECK)            | Public |
| GET     | `/api/info`                | Название и версия приложения                         | Public |
| POST    | `/api/auth/register`       | Регистрация → провайдер OpenRouter + токены         | Public |
| POST    | `/api/auth/login`          | Вход → пара токенов                                  | Public |
| POST    | `/api/auth/refresh`        | Новый access-токен по refresh-токену                 | Public |
| POST    | `/api/auth/logout`         | Отзыв refresh-токена                                  | Auth   |
| GET     | `/api/auth/me`             | Текущий пользователь                                 | Auth   |
| GET     | `/api/chats`               | Список чатов `?q=&filter=all\|today\|week\|month&limit=50&offset=0` | Auth |
| POST    | `/api/chats`               | Создать чат                                           | Auth   |
| GET     | `/api/chats/{id}`          | Чат + сообщения (`limit=500`)                        | Auth   |
| PATCH   | `/api/chats/{id}`          | Переименовать / сменить агента                       | Auth   |
| DELETE  | `/api/chats/{id}`          | Удалить чат и сообщения                               | Auth   |
| POST    | `/api/chats/{id}/messages` | Отправить сообщение (без стриминга)                  | Auth   |
| POST    | `/api/chats/{id}/stream`   | Отправить сообщение (SSE)                            | Auth   |
| GET/POST | `/api/providers`           | Список / создание провайдера                          | Auth   |
| PUT/DELETE | `/api/providers/{id}`     | Изменить / удалить провайдера                         | Auth   |
| GET/POST | `/api/models`              | Список / создание модели                              | Auth   |
| PUT/DELETE | `/api/models/{id}`        | Изменить / удалить модель                             | Auth   |
| GET/POST | `/api/agents`              | Список / создание агента                              | Auth   |
| PUT/DELETE | `/api/agents/{id}`        | Изменить / удалить агента                             | Auth   |

Форматы ответов:

- `/api/chats` → `{ items: [...], total, limit, offset }` (не массив!);
- `/api/providers`, `/api/models`, `/api/agents` → **массивы** объектов;
- `api_key` провайдера в ответе маскируется (`"********"`), реальное значение
  вернуть нельзя — при обновлении пустой или замаскированный ключ сохраняет старый.

---

## 6. Переменные окружения

| Переменная         | Значение по умолчанию       | Назначение                          |
|--------------------|-----------------------------|-------------------------------------|
| `JWT_SECRET`       | `baylang-dev-secret-change-me` | Секрет подписи JWT (HS256)        |
| `ACCESS_TOKEN_TTL` | `1800`                      | TTL access-токена, секунд            |
| `REFRESH_TOKEN_TTL`| `604800`                    | TTL refresh-токена, секунд           |
| `BCRYPT_ROUNDS`    | `12`                        | Раундов bcrypt                       |
| `DATABASE_PATH`    | `./data/baylang.sqlite3`    | Файл SQLite                          |
| `HOST`             | `0.0.0.0`                   | Хост uvicorn                         |
| `PORT`             | `8000`                      | Порт uvicorn                         |
| `LOG_LEVEL`        | `info`                      | Уровень логирования (`src/app.py`)  |

Доступ одинаков для `os.environ` (Docker) и bindings Workers — класс `Env` в
`core/config.py` умеет читать оба источника (`get`, `get_int`, `get_bool`, `require`).

---

## 7. Команды разработки

### Backend

```bash
pip install -r src/requirements.txt

cd src
uvicorn app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

`create_app()` — SQLite + раздача собранного SPA. `create_cloudflare_app(env)` — D1,
без статики, без lifespan (схема создаётся лениво).

### Frontend

```bash
cd src
npm install
npm run dev        # http://localhost:5173, /api проксируется на :8000 (API_URL)
npm run build      # сборка в src/dist (outDir "dist", корень Vite — src/)
```

### Docker

```bash
chmod +x build.sh
./build.sh docker          # собрать образ baylang-ai:latest
./build.sh docker-run      # собрать и запустить на :8000 (том ./data → /app/data)
./build.sh docker-logs     # логи
./build.sh docker-stop     # остановить и удалить
./build.sh docker-push     # отправить в реестр
./build.sh backend         # установить python-зависимости
./build.sh frontend        # npm install + npm run build
./build.sh dev             # backend :8000 + frontend :5173
./build.sh cloudflare      # сборка фронта + wrangler deploy
./build.sh clean           # удалить src/dist, __pycache__, ./data
./build.sh test            # pytest (тестов в репозитории пока нет)
```

Переменные окружения для `build.sh`: `IMAGE_NAME`, `IMAGE_TAG`, `CONTAINER_NAME`,
`HOST_PORT`, `DATA_DIR`, `DOCKER`, `JWT_SECRET`.

### Cloudflare Workers

```bash
cd src && npx wrangler d1 create baylang_ai   # создать базу
# вписать реальный database_id в src/wrangler.jsonc
./build.sh cloudflare
```

Worker: имя `baylang_ai`, `main: src/main.py`, флаг `python_workers`, binding D1 `DB`.

---

## 8. Известные проблемы и расхождения

Этот раздел — **фактическое состояние репозитория на момент последней проверки**.
Перед началом работы сверяйтесь с ним.

### 8.1 Тестов нет

`build.sh test` вызывает `pytest`, в `pyproject.toml` есть dev-группа
(`pytest`, `pytest-asyncio`, `httpx`), но каталога `tests/` в репозитории **нет**.
При добавлении тестов держитесь структуры `tests/` в корне и используйте
`container.reset()` + `container.instance(...)` для подмены зависимостей.

### 8.2 Мелочи

- `build.sh` объявляет `COMPOSE_FILE=docker-compose.yml`, но файла `docker-compose.yml`
  в репозитории нет — переменная не используется.
- `JWT_SECRET` имеет разные дефолты: `baylang-dev-secret-change-me` в `core/security.py`
  и `change-me-in-production` в `build.sh` (тоже dev-значения — в проде обязательно задавать явно).
- `core/routes/chats.py` отдаёт 403 на чужой чат, а 404 — в `ChatService._get_chat`;
  поведение при отсутствии чата различается между слоями, учитывайте это при отладке.

---

## 9. Соглашения по коду

### Python

- Отступы — **4 пробела**, максимальная длина строки ~100.
- Все модули начинают с `from __future__ import annotations` и содержат
  **русскоязычный docstring** с кратким описанием и `__all__` в конце.
- Типизация обязательна: аннотации аргументов и возвращаемых типов.
- Имена: модули/функции/переменные — `snake_case`, классы — `PascalCase`,
  константы — `UPPER_SNAKE_CASE`. Имена функций в `core/routes` — `snake_case`,
  а HTTP-методы и пути — в нижнем регистре (`/api/auth/register`).
- Строки — двойные кавычки.
- SQL — только в репозиториях, параметры — через `?`-плейсхолдеры (никогда не конкатенация).
- Ошибки API — `HTTPException` с русским текстом; бизнес-ошибки сервисов — собственные
  исключения (`AgentError`), которые маршрут превращает в 4xx.

### JavaScript / Vue

- Отступы — **4 пробела**, строки — двойные кавычки, semicolons обязательны.
- Стиль классов — как в `BasePageModel`: конструктор + методы с `this.`,
  без `this.` в static-методах.
- Стили — `<style scoped>` с BEM-подобными классами (`block__element--modifier`).
  Глобальные переменные темы — в `src/assets/main.css`.
- Логика — в модели, в `.vue` — только рендер и `@`-обработчики.
- Импорты — через алиас `@/` (он указывает на каталог `src/`).

### Комментарии и тексты

- Комментарии, docstring'и, сообщения об ошибках и UI-тексты — **на русском**.
- Идентификаторы в коде — английские.

---

## 10. Правила работы в репозитории

1. **Не обходить DI-контейнер.** Новые зависимости регистрируются в `core/app.py`
   (`register_repositories` / `register_services`) и достаются через
   `core/dependencies.py` + `Depends(...)`.
2. **SQL — только в `core/repositories/`.** В маршрутах и сервисах SQL не пишется.
3. **Схема БД меняется в `core/database/migrations.py`** — там единственный список DDL,
   общий для SQLite и D1. Используйте `IF NOT EXISTS`, чтобы миграция оставалась идемпотентной.
4. **Новый endpoint** → схема в `core/schemas/` → маршрут в `core/routes/`
   (префикс `/api`) → регистрация в `core/routes/__init__.py::register_all_routes`.
5. **Новая страница** → папка `pages/<Name>Page/` с `<Name>Page.vue` + `<Name>PageModel.js`,
   наследование от `BasePageModel`, регистрация маршрута в `AppLayoutModel.register_routes()`.
6. **Контекст pydantic-ai** сохраняется целиком через `to_jsonable_python` и
   восстанавливается через `ModelMessagesTypeAdapter` — не собирайте историю вручную.
7. **Все ответы с `api_key` маскируются** — не возвращайте ключ наружу.
8. **Не меняйте формат SSE-событий** (`delta` / `done` / `error` / `[DONE]`) без
   одновременной правки `ChatPageModel.streamMessage`.
9. **Комментарий в коде** объясняет *почему*, а не *что*.
10. **Обновляйте `README.md`**, если меняете публичное поведение (API, env, команды сборки).

---

## 11. Чек-лист перед завершением задачи

- [ ] Backend запускается: `cd src && uvicorn app:create_app --factory --reload`.
- [ ] `GET /api/health` отвечает `{"status":"ok", ...}`.
- [ ] Регистрация/вход выдают токены, `GET /api/auth/me` работает с Bearer-заголовником.
- [ ] Чат отвечает и сохраняет историю; `POST /api/chats/{id}/stream` отдаёт SSE-кадры.
- [ ] Настройки провайдеров/моделей/агентов сохраняются и читаются обратно.
- [ ] Нет прямого SQL вне `core/repositories/`.
- [ ] Новые зависимости зарегистрированы в контейнере.
- [ ] Миграции идемпотентны и работают и на SQLite, и на D1.
- [ ] Фронтенд собирается: `cd src && npm run build` → результат в `src/dist`.
- [ ] `README.md` актуален относительно изменений.

---

## Итог

Документ описывает проект **BayLang AI** — веб-приложение для чатов с ИИ-агентами на
FastAPI + pydantic-ai (backend) и Vue 3 (frontend), разворачиваемое в Docker или
Cloudflare Workers.

Зафиксированы: фактическая структура репозитория, четырёхслойная архитектура backend
(маршруты → сервисы → Record-репозитории → абстракция БД с общим списком миграций для
SQLite и D1), DI-контейнер с правилами регистрации зависимостей, механизм авторизации
(JWT + bcrypt + отзываемый refresh-токен), цикл агента pydantic-ai с сохранением полного
контекста и SSE-стримингом, паттерн frontend «страница = `.vue` + `Model.js»» с
собственным History-API роутером, полный справочник API и переменных окружения, команды
сборки и запуска, а также соглашения по стилю кода.

Отдельно и максимально честно описано **фактическое состояние репозитория**: тестов в
проекте нет, хотя инфраструктура для них предусмотрена; в `build.sh` объявлена
неиспользуемая переменная `COMPOSE_FILE`; дефолты `JWT_SECRET` в коде и в скрипте
различаются (оба — dev-значения); коды ответа на чужой/отсутствующий чат различаются между
слоями маршрутов и сервиса.

**Вывод:** `AGENTS.md` создан с нуля (файла в репозитории не было) и теперь служит
рабочим техническим описанием проекта. Он покрывает всё, что нужно знать агенту для
безопасной правки кода, и явно отделяет «как задумано» от «как сейчас», чтобы не
опираться на неверные пути. Расхождения по путям фронтенда (alias `@`, entry-point,
`outDir`, `COPY` в Dockerfile, отсутствовавший `@/services/api`, каталог npm-команд)
устранены: фронтенд и Docker-образ собираются из плоской раскладки `src/`.
