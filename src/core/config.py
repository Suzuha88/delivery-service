from pydantic_settings import BaseSettings, SettingsConfigDict


class _BaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="allow")


class PostgresSettings(_BaseSettings):
    DB_CLIENT: str = "+asyncpg"
    DB_PASSWORD: str
    DB_NAME: str
    DB_USER: str
    DB_HOST: str
    DB_PORT: int

    @property
    def database_url(self) -> str:
        return f"postgresql{self.DB_CLIENT}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def database_url_without_client(self) -> str:
        return self.database_url.replace(self.DB_CLIENT, "")


class RabbitSettings(_BaseSettings):
    RABBIT_USER: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    RABBIT_PORT: int
    AMQP_PORT: str

    @property
    def rabbit_url(self) -> str:
        return f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.AMQP_PORT}/"


class RedisSettings(_BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int


class ApiSettings(_BaseSettings):
    API_PORT: int


class LoggingSettings(_BaseSettings):
    LOG_LEVEL: str = "INFO"


db_settings = PostgresSettings()
rabbit_settings = RabbitSettings()
redis_settings = RedisSettings()
api_settings = ApiSettings()
logging_settings = LoggingSettings()
