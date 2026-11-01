# BayLang AI

**BayLang AI** — веб-приложение для общения с ИИ-агентами: чаты с сохранённой историей,
настройка провайдеров, моделей и «персон» (агентов).

**Стек:** FastAPI + pydantic-ai (backend) · Vue 3 + Vite (frontend) · SQLite / Cloudflare D1 · Docker / Cloudflare Workers

> 📘 **Структура проекта, справочник API, архитектура и правила работы с кодом описаны в
> [AGENTS.md](AGENTS.md).** Этот файл отвечает только на два вопроса: *что это за проект*
> и *как его запустить*.

---

## Возможности

- **Авторизация** — регистрация и вход по email + пароль, пара JWT-токенов
  (access + refresh), автоматическое обновление access-токена на фронтенде,
  разграничение доступа к данным пользователей.
- **Чат с агентом** — общение с «персоной» через pydantic-ai: полный контекст диалога
  сохраняется между запросами, ответ можно получать постепенно (SSE-стриминг) или целиком.
- **История чатов** — список последних 50 чатов с поиском по названию и фильтром
  (все / сегодня / неделя / месяц), переименование, переключение агента и удаление.
- **Настройка провайдеров** — название, URL и API-ключ. Для OpenRouter дополнительно
  задаётся список upstream-провайдеров через запятую (параметр `only`).
- **Настройка моделей** — привязка к провайдеру, имя LLM-модели, `temperature`, `max_tokens`.
- **Настройка агентов** — системный промпт + выбранная модель.

---

## Как это устроено (кратко)

Доменная цепочка выстроена последовательно: **провайдер → модель → агент → чат**.
Провайдер отвечает за доступ к LLM (URL + ключ), модель — за параметры генерации,
агент — за системный промпт, чат — за историю общения и сохранённый контекст pydantic-ai.

**Backend** — FastAPI с собственным DI-контейнером и строгим делением на слои:
маршруты → сервисы → Record-репозитории → абстракция базы данных. SQL живёт только
в репозиториях, схема БД — один общий список миграций для SQLite и Cloudflare D1.

**Frontend** — Vue 3 без внешнего роутера и UI-кита: собственный History-API роутер
и паттерн «страница = `.vue` + `Model.js`», где логика живёт в модели, а в компоненте —
только рендер.

**Хранилище** — SQLite локально и в Docker, Cloudflare D1 в Workers; интерфейс БД
одинаков, различается только реализация.

---

## Требования

| Для чего | Что нужно |
|----------|-----------|
| Backend | Python ≥ 3.12 |
| Frontend | Node.js ≥ 20 (в Docker-образе — `node:22-alpine`) |
| Docker-вариант | Docker Engine |
| Cloudflare-вариант | Аккаунт Cloudflare, `wrangler`, база D1 |

---

## Быстрый старт (Docker)

Docker-образ многостадийный: **node:22-alpine** собирает Vue-приложение в `src/dist`,
**python:3.12-slim** ставит зависимости и раздаёт собранный SPA вместе с API.

```bash
chmod +x build.sh

./build.sh docker        # собрать образ baylang-ai:latest
./build.sh docker-run    # собрать и запустить контейнер на :8000
./build.sh docker-logs   # смотреть логи
./build.sh docker-stop   # остановить и удалить контейнер
```

Приложение будет доступно на <http://localhost:8000>, данные SQLite — в томе
`./data` (в контейнере `/app/data`).

Перед публикацией задайте собственный секрет подписи токенов:

```bash
JWT_SECRET="ваш-длинный-секрет" ./build.sh docker-run
```

---

## Локальная разработка

Backend и frontend запускаются независимо, в двух терминалах.

### Backend

```bash
pip install -r src/requirements.txt

cd src
uvicorn app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

API доступно на <http://localhost:8000/api>, health-check — `GET /api/health`.
Схема БД создаётся автоматически при старте, файл — `data/baylang.sqlite3`
(переопределяется переменной `DATABASE_PATH`).

### Frontend

```bash
cd src
npm install
npm run dev        # http://localhost:5173, запросы /api проксируются на :8000
```

npm-команды выполняются **из каталога `src/`** — там лежат `package.json` и корень
Vite-сборки (`index.html`). Прокси можно перенаправить переменной `API_URL`:

```bash
API_URL=http://localhost:8000 npm run dev
```

### Одной командой

```bash
./build.sh dev       # установить зависимости, поднять backend :8000 и frontend :5173
```

### Сборка фронтенда отдельно

```bash
cd src && npm run build     # результат — в src/dist, его раздаёт FastAPI
```

---

## Первый запуск

1. Откройте приложение и зарегистрируйтесь — при регистрации автоматически создаётся
   провайдер **OpenRouter** (по умолчанию).
2. Откройте «Настройки → Провайдеры» и вставьте свой API-ключ OpenRouter.
3. Создайте модель (имя LLM, `temperature`, `max_tokens`) и агента (системный промпт + модель).
4. Создайте чат и начните общение.

Ключи провайдеров никогда не возвращаются наружу в открытом виде — в ответах API они
маскируются.

---

## Переменные окружения

| Переменная         | По умолчанию                    | Назначение                       |
|--------------------|---------------------------------|----------------------------------|
| `JWT_SECRET`       | `baylang-dev-secret-change-me`  | Секрет подписи JWT (HS256)       |
| `ACCESS_TOKEN_TTL` | `1800`                          | TTL access-токена, секунд         |
| `REFRESH_TOKEN_TTL`| `604800`                        | TTL refresh-токена, секунд        |
| `BCRYPT_ROUNDS`    | `12`                            | Раундов bcrypt                   |
| `DATABASE_PATH`    | `./data/baylang.sqlite3`         | Файл SQLite                      |
| `HOST`             | `0.0.0.0`                       | Хост uvicorn                     |
| `PORT`             | `8000`                          | Порт uvicorn                     |
| `LOG_LEVEL`        | `info`                          | Уровень логирования              |

Значения по умолчанию — **dev-значения**: в production задайте `JWT_SECRET` явно.
Для `build.sh` есть свои переменные: `IMAGE_NAME`, `IMAGE_TAG`, `CONTAINER_NAME`,
`HOST_PORT`, `DATA_DIR`, `DOCKER`, `JWT_SECRET`.

---

## Команды build.sh

| Команда               | Действие                                                |
|-----------------------|---------------------------------------------------------|
| `./build.sh backend`  | Установить Python-зависимости                           |
| `./build.sh frontend` | `npm install` + `npm run build` в `src/`                |
| `./build.sh dev`      | Локальный запуск: backend :8000 + frontend :5173         |
| `./build.sh docker`   | Собрать Docker-образ                                    |
| `./build.sh docker-run` | Собрать и запустить контейнер                          |
| `./build.sh docker-logs` / `docker-stop` / `docker-push` | Логи / остановка / отправка в реестр |
| `./build.sh cloudflare` | Сборка фронтенда + деплой в Cloudflare Workers         |
| `./build.sh test`     | `pytest` (тестов в репозитории пока нет)                |
| `./build.sh clean`    | Удалить `src/dist`, `node_modules`, `__pycache__`, `./data` |

---

## Деплой в Cloudflare Workers

Worker запускает backend на Python (`python_workers`), база — Cloudflare D1.

```bash
cd src && npx wrangler d1 create baylang_ai     # создать базу
# вписать реальный database_id в src/wrangler.jsonc
./build.sh cloudflare
```

Имя воркера — `baylang_ai`, точка входа — `src/main.py`, binding базы — `DB`.
Схема БД создаётся лениво при первом запросе.
