# Бэкенд системы доставки товаров.

### Запуск: 
`cat .env_example > .env && docker-compose build && docker-compose up`

### Настройка: 
переменные окружения описаны в .env file
при запуске fastAPI приложений через докер 
хосты контейнеров должны быть идентичны названиям сервисов
в docker-compose.yaml, при запуске без контейнеров, например

`docker-compose up -d sql_db redis rabbit_mq && python src/api_gateway/src/main.py`

хосты нужно переименовать в localhost

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
