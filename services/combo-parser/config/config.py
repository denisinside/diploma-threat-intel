from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    MONGODB_URI: str
    MONGODB_DB_NAME: str
    ELASTICSEARCH_HOSTS: str
    ELASTICSEARCH_INDEX_NAME_LEAKS: str
    ELASTICSEARCH_USERNAME: str = ""
    ELASTICSEARCH_PASSWORD: str = ""

    # Safety limits for archive extraction
    MAX_ARCHIVE_SIZE_BYTES: int = 4 * 1024 * 1024 * 1024
    MAX_FILE_COUNT_IN_ARCHIVE: int = 10_000
    SAFE_TEXT_EXTENSIONS: str = "txt,csv,json,log"
    DANGEROUS_EXTENSIONS: str = "exe,dll,bat,cmd,scr,ps1,vbs,js,com,pif,msi,sh"
    ES_BULK_SIZE: int = 20_000
    ES_REQUEST_TIMEOUT: int = 300  # seconds for bulk ops (large files need time)
    PARSE_WORKERS: int = 4  # parallel threads for parsing (0 = sequential)

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        extra="ignore",
    )

    @property
    def safe_text_extensions_set(self) -> set:
        return {e.strip().lower() for e in self.SAFE_TEXT_EXTENSIONS.split(",") if e.strip()}

    @property
    def dangerous_extensions_set(self) -> set:
        return {e.strip().lower() for e in self.DANGEROUS_EXTENSIONS.split(",") if e.strip()}


settings = Settings()
