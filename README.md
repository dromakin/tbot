# tbot-kib

Telegram-бот для курсов КИБа с админ панелью в Telegram Mini Apps

## Возможности

- регистрация на лекции по `tg_user_id`;
- выдача ссылки на Яндекс.Телемост только зарегистрированным;
- сбор посещаемости через клики по кнопке получения ссылки;
- экспорт статистики в CSV;
- Mini App для админов (статистика, создание лекций, управление регистрацией, обновление доп. материалов).

## Стек

- Python 3.12
- aiogram 3
- FastAPI + uvicorn
- SQLAlchemy 2 + Alembic
- APScheduler
- React + Vite + TypeScript
- PostgreSQL
- Caddy (для VPS) / Railway (managed deployment)

## Локальный запуск (бот + Mini App)

### Подготовка

1. Установить зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
make install
```

2. Создать `.env` из примера:

```bash
cp .env.example .env
```

3. Настроить `DB_DSN` в `.env` (выберите один вариант):

```env
# Рекомендуется для локальной разработки (бот запускается с хоста)
DB_DSN=sqlite+aiosqlite:///./bot.db

# Если бот и БД запускаются внутри docker compose
DB_DSN=postgresql+asyncpg://tbot:tbot@db:5432/tbot

# Если бот запускается с хоста, а Postgres локально на хосте
DB_DSN=postgresql+asyncpg://tbot:tbot@localhost:5432/tbot
```

`@db` резолвится только внутри сети `docker compose`. Для `make dev-bot` с хоста используйте SQLite или `localhost`.

4. Важно для `.env`:

- Если `WEB_DEV_AUTH_BYPASS=false`, можно оставить `WEB_DEV_USER_ID` пустым или `0`.
- Тексты бота берутся из `graph-src/*.json`.
- Ссылки на материалы задаются через админ-панель Mini App:
  - общая ссылка — вкладка `Настройки`;
  - ссылка конкретной лекции — вкладка `Лекции`.

5. Применить миграции:

```bash
make migrate
```

`make migrate` использует тот же DSN, что и `make dev-bot` (переменные `DATABASE_URL`/`DB_DSN` из окружения и `.env`).

6. Запустить бота:

```bash
make dev-bot
```

### Сценарий A: prod-like + туннель

Используйте этот режим, если хотите поведение, максимально близкое к продакшену.

```bash
make build-front
make dev-bot
```

После запуска поднимите туннель на FastAPI (`:8080`):

```bash
# Вариант 1: cloudflared
make dev-tunnel-cf PORT=8080

# Вариант 2: ngrok
make dev-tunnel-ngrok PORT=8080
```

Дальше:
- возьмите HTTPS URL туннеля и установите его в `.env` как `WEB_PUBLIC_URL`;
- перезапустите `make dev-bot`;
- в `@BotFather` (`Configure Mini App`) задайте тот же HTTPS URL.

### Сценарий B: Vite dev + туннель (HMR)

Подходит для активной разработки интерфейса.

Терминал 1:

```bash
make dev-bot
```

Терминал 2:

```bash
make dev-front
```

Терминал 3 (туннель на Vite `:5173`):

```bash
# Вариант 1: cloudflared
make dev-tunnel-cf PORT=5173

# Вариант 2: ngrok
make dev-tunnel-ngrok PORT=5173
```

В этом режиме Vite проксирует `/api` и `/healthz` на `http://localhost:8080`.
Укажите URL туннеля в `WEB_PUBLIC_URL` и в `@BotFather`.

### Сценарий C: dev-bypass в обычном браузере

Используйте только локально для быстрой проверки UI без Telegram клиента.

В `.env`:

```env
WEB_DEV_AUTH_BYPASS=true
WEB_DEV_USER_ID=123456789
WEB_DEV_USER_USERNAME=dev_admin
```

Далее:

```bash
make dev-bot
make dev-front
```

Откройте `http://localhost:5173`. При включенном bypass backend принимает запросы без `initData`.
На старте бот пишет WARNING, что bypass активирован.

Перед деплоем обязательно отключите:

```env
WEB_DEV_AUTH_BYPASS=false
```

### API через curl/Postman

Чтобы получить валидный `initData` для ручных запросов:

```bash
python scripts/make_init_data.py --user-id 111111111 --username admin_user
```

Пример запроса:

```bash
INIT_DATA=$(python scripts/make_init_data.py --user-id 111111111 --username admin_user)
curl -H "Authorization: tma ${INIT_DATA}" http://localhost:8080/api/me
```

## Деплой

Подробные инструкции по деплою и запуску через Docker вынесены в [DEPLOYMENT.md](DEPLOYMENT.md):

- локальный Docker (`docker-compose.local.yml`);
- VPS с Caddy (`docker-compose.vps.yml`);
- Railway (`Dockerfile` + `railway.json`).

## Mini App в BotFather

1. Открыть `@BotFather` -> `/mybots` -> ваш бот.
2. `Bot Settings` -> `Configure Mini App`.
3. Указать URL Mini App: `https://<ваш-домен>`.
4. (Опционально) `Menu Button` -> URL `https://<ваш-домен>/admin`.

## Основные команды в боте

- `/start`, `/menu` — главное меню.
- `/admin` — список админ-команд.
- `/lecture_registrations <lecture_id>` — список регистраций по лекции.
- `/stats` — сводка регистрации и кликов.
- `/export_csv` — выгрузка `stats.csv`.

## Тесты

```bash
make test
```

## Troubleshooting

- `401 Missing Telegram Mini App authorization`:
  - Mini App открыта не внутри Telegram;
  - или выключен `WEB_DEV_AUTH_BYPASS` в сценарии C.
- `401 Invalid initData signature`:
  - `BOT_TOKEN` в `.env` не совпадает с токеном бота, через которого открыта Mini App.
- `403 Admin access required`:
  - ваш `tg_user_id` не добавлен в `ADMIN_IDS`.
- Ошибки CORS:
  - проверьте `WEB_PUBLIC_URL` (должен совпадать с origin туннеля);
  - после изменения `.env` перезапустите `make dev-bot`.
- Конфликт webhook (`TelegramConflictError`):
  - проверьте запуск через `python -m bot`/`make dev-bot`, webhook снимается автоматически на старте polling.
