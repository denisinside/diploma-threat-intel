from __future__ import annotations

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    RABBITMQ_URL: str
    RABBITMQ_EXCHANGE: str = "notifications.events"
    RABBITMQ_QUEUE: str = "notification_events"
    RABBITMQ_DLQ: str = "notification_events.dlq"
    RABBITMQ_MAX_RETRIES: int = 5

    MONGODB_URI: str
    MONGODB_DB_NAME: str

    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_USE_TLS: bool = True

    REQUEST_TIMEOUT_SECONDS: int = 15

    model_config = SettingsConfigDict(
        env_file="../../.env",
        extra="ignore",
    )


settings = Settings()
