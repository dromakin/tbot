# tbot-kib

Telegram-бот для курса КИБ:

- регистрация на лекции по `tg_user_id`;
- выдача ссылки на Яндекс.Телемост только зарегистрированным;
- сбор посещаемости через клики кнопки получения ссылки;
- экспорт статистики в CSV.

## Стек

- Python 3.12
- aiogram 3
- SQLAlchemy 2 + Alembic
- APScheduler
- PostgreSQL (prod) / SQLite (dev)

## Быстрый старт (локально)

1. Установить зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Создать `.env` из примера:

```bash
cp .env.example .env
```

3. Применить миграции:

```bash
alembic upgrade head
```

4. Запустить бота:

```bash
python -m bot
```

## Запуск в Docker

1. Заполнить `.env` (особенно `BOT_TOKEN` и `DB_DSN` для postgres).
2. Поднять сервисы:

```bash
docker compose up --build
```

## Основные команды в боте

- `/start`, `/menu` — открыть главное меню.
- Регистрация на лекции — через inline-кнопки и `tg_user_id`.
- Получение ссылки на онлайн-лекцию — кнопка в карточке лекции.
- Проверка статуса — список всех регистраций пользователя.

## Админ-команды

- `/admin` — помощь по админ-командам.
- `/create_lecture` — создание лекции через FSM.
- `/lectures` — список лекций.
- `/open_registration <lecture_id>`
- `/close_registration <lecture_id>`
- `/set_stream <lecture_id> <url>`
- `/set_materials <lecture_id> <url>`
- `/delete_lecture <lecture_id>`
- `/stats` — сводка регистрации и кликов.
- `/export_csv` — выгрузка `stats.csv`.

## Тесты

```bash
pytest
```
