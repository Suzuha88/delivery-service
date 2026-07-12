from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DB_CLIENT: str = "+asyncpg"
    DB_PASSWORD: str
    DB_NAME: str
    DB_USER: str
    DB_HOST: str
    DB_PORT: int

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql{self.DB_CLIENT}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def DATABASE_URL_WITHOUT_CLIENT(self) -> str:
        return self.DATABASE_URL.replace(self.DB_CLIENT, "")


settings = Settings()
