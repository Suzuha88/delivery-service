Initialise database on first launch:
souce .venv/bin/activate
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
