from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./f1hub.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    api_v1_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"


settings = Settings()
