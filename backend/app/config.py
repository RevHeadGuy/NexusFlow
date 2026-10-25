from functools import lru_cache
import secrets

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
    auth_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48), min_length=32)
    auth_token_expire_minutes: int = 720

    # Base URL of the frontend, used to build invitation links in emails the
    # backend sends. The browser derives its own origin, but the server cannot.
    frontend_base_url: str = "http://localhost:3000"

    # Email (SMTP) delivery for project invitations. Disabled by default so the
    # app runs without a mail server; when disabled, invites still return a link
    # to copy manually. Set email_enabled=true and the SMTP values to send mail.
    email_enabled: bool = False
    email_from: str = "NexusFlow <no-reply@nexusflow.local>"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_timeout_seconds: int = 15

    # Cross-process agent-to-agent (A2A) handoff. When enabled, each A2A message
    # is also POSTed to an external endpoint (webhook) in addition to the
    # persisted in-process bus, so agents in another service can receive it.
    # Disabled by default; the in-process bus is always the source of truth.
    a2a_external_delivery_enabled: bool = False
    a2a_webhook_url: str | None = None
    a2a_webhook_token: str | None = None
    a2a_webhook_timeout_seconds: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
