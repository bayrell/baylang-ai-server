# BayLang AI Server

**BayLang AI** — веб-приложение для общения с ИИ-агентами: чаты с историей, настройка провайдеров, моделей и агентов.

**Стек:** FastAPI (Cloudflare Workers / Docker) · Vue 3 · pydantic-ai · D1 / SQLite

## Функционал

- **Авторизация** — регистрация и вход по email + пароль, JWT-токены (access + refresh), разграничение доступа к данным пользователей.
- **Чат с пользователем** — общение с ИИ-агентом через pydantic-ai, с опциональным стримингом ответа (SSE).
- **История чатов** — select list с последними **50 чатами**, фильтр и поиск по названию, возможность создать новый чат.
- **Настройка агентов** — «персона» бота: системный промпт + выбранная модель.
- **Настройка моделей** — название модели, провайдер, температура, max_tokens и т.п.
- **Настройка провайдеров** — название, URL, API key. Провайдер по умолчанию — **OpenRouter**, у которого есть возможность задать список upstream-провайдеров через запятую (параметр `only`).

## Структура проекта

```
src/
├── app.py                  Точка входа для Docker (uvicorn app:create_app --factory)
├── main.py                 Точка входа для Cloudflare Workers
├── main.js                 Точка входа Vue-приложения
├── App.vue                 Корневой компонент
├── core/                   Ядро Python (DI, БД, репозитории, сервисы, маршруты)
│   ├── container.py        DI-контейнер: register / singleton / get
│   ├── app.py              Сборка FastAPI-приложения
│   ├── auth.py             Регистрация / вход / refresh / logout
│   ├── security.py         bcrypt + JWT
│   ├── database/           Абстракция БД: SQLite и Cloudflare D1
│   ├── repositories/       Record-репозитории (SQL-запросы)
│   ├── schemas/            Pydantic-схемы API
│   ├── services/           ChatService, AgentFactory, провайдеры/модели
│   └── routes/             API-маршруты (/api/...)
├── lib/Router.js           Простой роутер (url → route → модель страницы)
├── layouts/                AppLayoutModel + AppLayout.vue
├── pages/                  Страницы: пара «<Name>Page.vue» + «<Name>PageModel.js»
├── services/               API-клиент с авто-обновлением токена
├── assets/                 Стили
└── dist/                   Сборка Vue (генерируется Vite)
```

## API

| Метод  | URL                         | Описание                        | Доступ |
|--------|-----------------------------|---------------------------------|--------|
| POST   | `/api/auth/register`        | Регистрация                     | Public |
| POST   | `/api/auth/login`           | Вход, выдача токенов            | Public |
| POST   | `/api/auth/refresh`         | Обновление access-токена        | Public |
| POST   | `/api/auth/logout`          | Инвалидация refresh-токена      | Auth   |
| GET    | `/api/auth/me`              | Текущий пользователь            | Auth   |
| GET    | `/api/chats`                | Список чатов (`q`, `filter`, `limit=50`) | Auth |
| POST   | `/api/chats`                | Создать чат                     | Auth   |
| GET    | `/api/chats/{id}`           | Чат с сообщениями               | Auth   |
| PATCH  | `/api/chats/{id}`           | Переименовать / сменить агента  | Auth   |
| DELETE | `/api/chats/{id}`           | Удалить чат                     | Auth   |
| POST   | `/api/chats/{id}/messages`  | Сообщение агенту (без стриминга)| Auth   |
| POST   | `/api/chats/{id}/stream`    | Сообщение агенту (SSE)          | Auth   |
| GET/POST/PUT/DELETE | `/api/providers`   | Провайдеры                      | Auth   |
| GET/POST/PUT/DELETE | `/api/models`      | Модели                          | Auth   |
| GET/POST/PUT/DELETE | `/api/agents`      | Агенты                          | Auth   |
| GET    | `/api/health`               | Health-check                    | Public |

## Переменные окружения

| Переменная        | По умолчанию                  | Назначение                        |
|-------------------|-------------------------------|-----------------------------------|
| `JWT_SECRET`      | `baylang-dev-secret-change-me`| Секрет подписи JWT                |
| `ACCESS_TOKEN_TTL`| `1800`                        | TTL access-токена, сек             |
| `REFRESH_TOKEN_TTL`| `604800`                      | TTL refresh-токена, сек            |
| `DATABASE_PATH`   | `./data/baylang.sqlite3`      | Путь к SQLite-файлу               |
| `PORT` / `HOST`   | `8000` / `0.0.0.0`            | Параметры запуска                 |

## Сборка и запуск

### Docker (рекомендуется)

```bash
chmod +x build.sh

./build.sh docker        # собрать образ baylang-ai:latest
./build.sh docker-run    # собрать и запустить контейнер на :8000
./build.sh docker-logs   # логи контейнера
./build.sh docker-stop   # остановить и удалить контейнер
./build.sh docker-push   # отправить образ в реестр
```

Образ многостадийный: **node:22-alpine** собирает Vue-приложение в `src/dist`, **python:3.12-slim** ставит зависимости и раздаёт собранный SPA вместе с API. Данные SQLite хранятся в томе `/app/data`.

### Локальная разработка

```bash
# Backend
pip install -r src/requirements.txt
cd src && uvicorn app:create_app --factory --reload --port 8000

# Frontend (в отдельном терминале)
npm install
npm run dev        # http://localhost:5173, /api проксируется на :8000
```

### Cloudflare Workers

```bash
./build.sh cloudflare
```

Перед деплоем укажите реальный `database_id` в `src/wrangler.jsonc` и создайте базу: `wrangler d1 create baylang_ai`.

## Итог

Реализован полный функционал **BayLang AI** по пяти модулям ТЗ:

- **Авторизация** — JWT (access + refresh) с bcrypt-хешированием паролей, защита маршрутов через `Depends(get_current_user)` и автоматическое обновление токена на фронте.
- **Онлайн-чат** — агент-цикл pydantic-ai с восстановлением полного контекста из `all_messages()`, стриминг через SSE и историей из последних 50 чатов с поиском и фильтром.
- **Провайдеры** — название, URL и API-ключ; для OpenRouter дополнительно список upstream-провайдеров через запятую (`only`), маппится в `OpenRouterProviderConfig`.
- **Модели** — связка «провайдер + название LLM-модели + температура/max_tokens», применяется через `OpenRouterModelSettings`.
- **Агенты** — системный промпт + выбранная модель; сборка выполняется фабрикой агентов, зарегистрированной в DI-контейнере.

**Вывод:** архитектура полностью соответствует ТЗ — единый DI-контейнер связывает Record-репозитории, сервисы и pydantic-схемы, а фронтенд следует паттерну «страница + модель» на Vue 3 с собственным роутером. Backend и Frontend собираются раздельно и поставляются единым Docker-образом.
