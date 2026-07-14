Initialise database on first launch:
souce .venv/bin/activate
alembic -c packages/shared/src/shared/alembic.ini revision --autogenerate -m "Initial migration"
alembic -c packages/shared/src/shared/alembic.ini upgrade head

