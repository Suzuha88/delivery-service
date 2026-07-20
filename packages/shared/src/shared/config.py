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
    AMQP_PORT: int

    REDIS_HOST: str
    REDIS_PORT: int

    API_GATEWAY_PORT: int
    MQ_CONSUMER_PORT: int

    LOG_LEVEL: str = "INFO"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql{self.DB_CLIENT}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_WITHOUT_CLIENT(self) -> str:
        return self.DATABASE_URL.replace(self.DB_CLIENT, "")

    @property
    def RABBIT_URL(self) -> str:
        return f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.AMQP_PORT}/"


settings = Settings()
