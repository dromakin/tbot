# Deployment Guide

Проект поддерживает 3 сценария развертывания:

1. локально через Docker;
2. VPS (Ubuntu) с Caddy и собственным доменом;
3. Railway (managed Postgres + auto HTTPS).

## Общие переменные окружения

Минимально обязательные переменные:

- `BOT_TOKEN`
- `ADMIN_IDS`
- `WEB_PUBLIC_URL`
- `TZ`

База данных:

- локально/VPS: используйте `DB_DSN`;
- Railway: используйте `DATABASE_URL` (инжектируется Railway Postgres автоматически).

Тексты сообщений берутся из `graph-src/*.json`.
Ссылки на материалы задаются в админке Mini App и хранятся в БД.

## 1) Локальный Docker (bot + Postgres)

Файл: `docker-compose.local.yml`.

Запуск:

```bash
cp .env.example .env
docker compose -f docker-compose.local.yml up --build
```

Что поднимется:

- `bot` (polling + scheduler + FastAPI);
- `db` (PostgreSQL 16).

Порты:

- `8080` — FastAPI/Mini App;
- `5432` — Postgres.

## 2) VPS (Ubuntu + Caddy)

Файл: `docker-compose.vps.yml`.

Шаги:

1. Подготовьте VPS с Docker + Docker Compose plugin.
2. Пропишите A-запись домена на IP сервера.
3. Склонируйте репозиторий и создайте `.env`.
4. Укажите:
   - `DOMAIN=ваш_домен`
   - `WEB_PUBLIC_URL=https://ваш_домен`
   - `DB_DSN=postgresql+asyncpg://tbot:tbot@db:5432/tbot`
5. Запустите:

```bash
docker compose -f docker-compose.vps.yml up -d --build
```

Проверка логов:

```bash
docker compose -f docker-compose.vps.yml logs -f bot
docker compose -f docker-compose.vps.yml logs -f caddy
```

Caddy автоматически выпускает и продлевает TLS-сертификаты.

## 3) Railway

Файлы: `Dockerfile`, `railway.json`, `deploy/entrypoint.sh`.

Архитектура:

- один Railway сервис приложения (`bot`) с Docker build;
- managed Postgres как отдельный Railway service/plugin;
- `DATABASE_URL` и `PORT` приходят из Railway.

Шаги:

1. Создайте новый проект в Railway и подключите репозиторий.
2. Добавьте Postgres service в этом же проекте.
3. Убедитесь, что у app service доступен `DATABASE_URL`.
4. В Variables app service задайте:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
   - `WEB_PUBLIC_URL` (временно можно оставить пустым)
   - `TZ=Europe/Moscow`
   - `WEB_DEV_AUTH_BYPASS=false`
5. В Networking сгенерируйте публичный домен вида `*.up.railway.app`.
6. Обновите `WEB_PUBLIC_URL` на этот домен (с `https://`).
7. Запустите деплой (Railway использует `Dockerfile` и `railway.json`).
8. После первого запуска откройте админку Mini App:
   - вкладка `Настройки` -> заполните общую ссылку на материалы;
   - вкладка `Лекции` -> при необходимости обновите `stream_url` и `materials_url` для конкретных лекций.
9. Не задавайте одновременно `DATABASE_URL` и `DB_DSN` с разными значениями:
   `alembic` и runtime должны смотреть в одну и ту же БД.

Во время старта контейнера выполняется:

1. `alembic upgrade head`
2. `python -m bot`

`alembic` использует `DATABASE_URL` (или `DB_DSN`) из окружения.
Значение из `alembic.ini` применяется только как fallback.
Это делает запуск идемпотентным для миграций.

## BotFather (для всех сценариев)

1. Откройте `@BotFather` -> `/mybots` -> ваш бот.
2. `Bot Settings` -> `Configure Mini App`.
3. Укажите `WEB_PUBLIC_URL`.
4. При необходимости настройте menu button на `/admin`.

## Railway reference compose

Файл `docker-compose.railway.yml` добавлен как референс структуры окружения.
Реальный деплой на Railway использует `Dockerfile` + `railway.json` (а не `docker compose up`).

## Troubleshooting

- `Invalid initData signature`:
  - проверьте, что `BOT_TOKEN` совпадает с ботом, через который открыта Mini App.
- `Admin access required`:
  - добавьте ваш `tg_user_id` в `ADMIN_IDS`.
- База не подключается на Railway:
  - проверьте наличие `DATABASE_URL` в Variables app service;
  - убедитесь, что схема преобразуется в `postgresql+asyncpg://` на старте.
- `relation "..." does not exist` на старте scheduler/bot:
  - миграции, вероятно, применились не в ту БД;
  - проверьте, что нет конфликтующего ручного `DB_DSN`, который перебивает `DATABASE_URL`;
  - выполните redeploy после выравнивания переменных.
- Healthcheck fail:
  - проверьте, что `WEB_ENABLED=true`;
  - endpoint `GET /healthz` должен отдавать `200`.
