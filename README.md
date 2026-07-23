# Бэкенд системы доставки товаров.

### Запуск: 
в докере:
`cat .env_example > .env && docker-compose build && docker-compose up`
на локальной машине:
`cat .env.local_example > .env.local`
`docker compose up -d postgres redis rabbit`
`python manage.py run_consumer`
`python manage.py run_api`
после этого необходимо выполнить миграции через алембик с помощью
`alembic upgrade head`
если алембик не установлен глобально см. пункт Установка

### Настройка: 
переменные окружения описаны в .env.local и .env файлах
первый для запуска на локальной машине
второй для запуска в докере

уровень логирования указывается в переменной LOG_LEVEL

### Установка:

1. установить uv: https://docs.astral.sh/uv/getting-started/installation/
2. `uv sync`
3. `source .venv/bin/activate`

### Тесты:
`uv sync --group dev`
`pytest tests -v`

### Стэк:
FastAPI, SQLAlchemy async + asyncpg, Alembic, aio-pika, Redis, pydantic-settings, uv, FastStream.

### API:
после запуска можно посмотреть документацию по ссылке:
http://localhost:8000/docs#/
