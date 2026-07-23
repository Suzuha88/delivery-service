FROM astral/uv:python3.14-trixie-slim@sha256:b6e3a8825dfb232a6b962228f0b5cf98ee1d2b4263f62c2639f68887f4e634a2 AS base
WORKDIR /app
COPY pyproject.toml pyproject.toml 
COPY src/ src/
COPY manage.py manage.py
RUN uv pip install --system .

ENV PYTHONUNBUFFERED=1

FROM base AS api
ENTRYPOINT ["python", "manage.py", "run_api"]

FROM base AS consumer
ENTRYPOINT ["python", "manage.py", "run_consumer"]
