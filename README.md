# Бэкенд системы доставки товаров.

### Запуск: 
`cat .env_example.docker > .env.docker && docker-compose build && docker-compose up`
после этого необходимо выполнить миграции через алембик с помощью
`alembic upgrade head`
если алембик не установлен глобально см. пункт Установка

### Настройка: 
переменные окружения описаны в .env и .env.docker файлах
первый для запуска на локальной машине:
`docker compose -d postgres redis rabbit`
`python manage.py run_consumer`
`python manage.py run_producer`
второй для запуска в докере:
`docker compose build && docker compose up`

уровень логирования указывается в переменной LOG_LEVEL

### Установка:

1. установить uv: https://docs.astral.sh/uv/getting-started/installation/
2. `uv sync`
3. `source .venv/bin/activate`

### Тесты:
`pytest tests -v`

### Стэк:
FastAPI, SQLAlchemy async + asyncpg, Alembic, aio-pika, Redis, pydantic-settings, uv.

### API:
после запуска можно посмотреть документацию по ссылке:
http://localhost:8000/docs#/
