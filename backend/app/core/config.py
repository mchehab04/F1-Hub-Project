from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite:///./f1hub.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    api_v1_prefix: str = "/api/v1"


settings = Settings()
