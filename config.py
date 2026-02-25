from datetime import date

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")
    webhook_host: str = Field(..., alias="WEBHOOK_HOST")
    webhook_path: str = Field("/webhook", alias="WEBHOOK_PATH")
    curator_chat_id: int = Field(..., alias="CURATOR_CHAT_ID")
    closed_chat_id: int = Field(..., alias="CLOSED_CHAT_ID")

    # Payment
    payment_link: str = Field(..., alias="PAYMENT_LINK")
    payment_webhook_secret: str = Field(..., alias="PAYMENT_WEBHOOK_SECRET")
    payment_webhook_path: str = Field("/payment", alias="PAYMENT_WEBHOOK_PATH")

    # Database — Railway даёт postgresql://, нужен postgresql+asyncpg://
    database_url: str = Field(..., alias="DATABASE_URL")

    @computed_field
    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # Program
    program_start_date: date = Field(..., alias="PROGRAM_START_DATE")

    # Dev
    dev_mode: bool = Field(False, alias="DEV_MODE")

    @computed_field
    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_host}{self.webhook_path}"


settings = Settings()
