import asyncio

import uvicorn
from typer import Typer

from src.core.api import setup_api
from src.core.config import api_settings
from src.core.consumer import main

manager = Typer()


@manager.command("run_api")
def run_api() -> None:
    setup_api()
    uvicorn.run(
        "src.core.api:app",
        host="0.0.0.0",
        port=api_settings.API_PORT,
        reload=True,
    )


@manager.command("run_consumer")
def run_consumer() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    manager()
