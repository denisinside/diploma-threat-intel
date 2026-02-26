from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_SESSION_NAME: str = "leak_scraper_session"
    TELEGRAM_SESSION_PATH: str = ""  # Optional: full path for .session (for Docker volume)
    LEAK_SCRAPER_CHANNELS: str = ""  # Comma-separated channel IDs, e.g. "-100123,-100456"
    API_GATEWAY_URL: str = "http://localhost:8000"
    STORAGE_PATH: str = "storage"
    ALLOWED_EXTENSIONS: str = "txt,csv,zip,7z,rar"
    WATCHER_INTERVAL_MINUTES: int = 5
    MAX_CONCURRENT_DOWNLOADS: int = 3
    MESSAGE_BATCH_DELAY_SECONDS: float = 4.0
    MESSAGE_BATCH_SIZE: int = 50  # Pause after every N messages
    CHANNEL_DELAY_SECONDS: float = 3.0  # Delay between channels
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file="../../.env",
        extra="ignore",
    )

    @property
    def channels_list(self) -> List[str]:
        return [c.strip() for c in self.LEAK_SCRAPER_CHANNELS.split(",") if c.strip()]

    @property
    def allowed_extensions_set(self) -> set:
        return {ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()}


settings = Settings()
