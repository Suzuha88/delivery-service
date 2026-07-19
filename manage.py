import uvicorn
from typer import Typer

from src.config import settings
from src.consumer import setup_consumer
from src.producer import setup_producer

manager = Typer()


@manager.command("run_producer")
def run_producer() -> None:
    setup_producer()
    uvicorn.run("src.producer:app",
                port=settings.API_GATEWAY_PORT, reload=True)


@manager.command("run_consumer")
def run_consumer() -> None:
    setup_consumer()
    uvicorn.run("src.consumer:app",
                port=settings.MQ_CONSUMER_PORT, reload=True)


if __name__ == "__main__":
    manager()
