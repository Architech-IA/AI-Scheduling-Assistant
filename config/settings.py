from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str = Field(..., env="ANTHROPIC_API_KEY")
    model_triage: str = "claude-haiku-4-5-20251001"
    model_confirm: str = "claude-sonnet-4-6"
    max_tokens: int = 1024
    max_history_turns: int = 8  # truncar historial para controlar costos

    # Telegram
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")

    # WhatsApp
    whatsapp_api_key: str = Field("", env="WHATSAPP_API_KEY")
    whatsapp_phone_number_id: str = Field("", env="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_verify_token: str = Field("verify123", env="WHATSAPP_VERIFY_TOKEN")

    # Google
    google_credentials_path: str = Field("config/google_credentials.json", env="GOOGLE_CREDENTIALS_PATH")
    google_sheets_id: str = Field(..., env="GOOGLE_SHEETS_ID")

    # Redis
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    session_ttl_days: int = Field(30, env="SESSION_TTL_DAYS")

    # Servidor
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")
    base_url: str = Field(..., env="BASE_URL")

    # App
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    firma_nombre: str = Field("Firma de Abogados", env="FIRMA_NOMBRE")

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
