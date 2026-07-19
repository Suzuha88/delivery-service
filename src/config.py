from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    DB_CLIENT: str = "+asyncpg"
    DB_PASSWORD: str
    DB_NAME: str
    DB_USER: str
    DB_HOST: str
    DB_PORT: int

    RABBIT_USER: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    RABBIT_PORT: int
    AMQP_PORT: str

    REDIS_HOST: str
    REDIS_PORT: str

    API_GATEWAY_PORT: int
    MQ_CONSUMER_PORT: int

    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        return f"postgresql{self.DB_CLIENT}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def database_url_without_client(self) -> str:
        return self.database_url.replace(self.DB_CLIENT, "")

    @property
    def rabbit_url(self) -> str:
        return f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.AMQP_PORT}/"


settings = Settings()
