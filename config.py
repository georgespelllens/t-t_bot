import base64
import json
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

    # Google Sheets
    google_sheet_id: str = Field(..., alias="GOOGLE_SHEET_ID")
    google_credentials_json_b64: str = Field(..., alias="GOOGLE_CREDENTIALS_JSON")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Program
    program_start_date: date = Field(..., alias="PROGRAM_START_DATE")

    # Dev
    dev_mode: bool = Field(False, alias="DEV_MODE")

    @computed_field
    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_host}{self.webhook_path}"

    @computed_field
    @property
    def google_credentials_dict(self) -> dict:
        decoded = base64.b64decode(self.google_credentials_json_b64).decode("utf-8")
        return json.loads(decoded)


settings = Settings()
