from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

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


class RabbitSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    RABBIT_USER: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    RABBIT_PORT: int
    AMQP_PORT: str

    @property
    def rabbit_url(self) -> str:
        return f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.AMQP_PORT}/"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    REDIS_HOST: str
    REDIS_PORT: int


class ProducerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PRODUCER_PORT: int


class ConsumerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    CONSUMER_PORT: int


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    LOG_LEVEL: str = "INFO"


db_settings = PostgresSettings()
rabbit_settings = RabbitSettings()
redis_settings = RedisSettings()
producer_settings = ProducerSettings()
consumer_settings = ConsumerSettings()
logging_settings = LoggingSettings()
