from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NexusFlow"
    environment: str = "development"
    debug: bool = True
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "sqlite:///./nexusflow.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    llm_provider: str = "bedrock"
    llm_model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    aws_region: str = "us-west-2"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    llm_api_key: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    llm_timeout_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
