from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"

class Settings(BaseSettings):
    MONGODB_URI: str
    MONGODB_DB_NAME: str

    ELASTICSEARCH_HOSTS: str
    ELASTICSEARCH_INDEX_NAME_VULNERABILITIES: str
    ELASTICSEARCH_INDEX_NAME_LEAKS: str

    RABBITMQ_URL: str
    RABBITMQ_NOTIFICATIONS_EXCHANGE: str = "notifications.events"
    
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        extra="ignore",
    )

settings = Settings()