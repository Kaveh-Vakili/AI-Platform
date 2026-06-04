"""App-wide settings loaded from environment variables / .env file."""
from __future__ import annotations
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://stratos:stratos@localhost/stratos"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
