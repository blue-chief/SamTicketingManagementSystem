"""Application settings – all Appendix B variables."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Database & infrastructure ---
    DATABASE_URL: str = "postgresql+asyncpg://sam:sam@postgres:5432/ticketing"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: SecretStr = SecretStr("CHANGE_ME_IN_PRODUCTION")
    APP_BASE_URL: str = "http://localhost:8000"

    # --- IMAP ---
    IMAP_HOST: str = ""
    IMAP_PORT: int = 993
    IMAP_USER: str = ""
    IMAP_PASSWORD: SecretStr = SecretStr("")
    IMAP_FOLDER: str = "INBOX"
    IMAP_POLL_SECONDS: int = 30

    # --- SMTP ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: SecretStr = SecretStr("")
    SMTP_FROM: str = ""

    # --- SMS ---
    SMS_PROVIDER: str = ""
    SMS_API_KEY: SecretStr = SecretStr("")
    SMS_SENDER_ID: str = ""

    # --- WhatsApp ---
    WHATSAPP_API_KEY: SecretStr = SecretStr("")
    WHATSAPP_PHONE_ID: str = ""

    # --- AI / Analysis ---
    AI_BACKEND: str = "baseline"
    CONFIDENCE_THRESHOLD: float = 0.60
    DUPLICATE_SIMILARITY: float = 0.92
    SIMILAR_LINK_SIMILARITY: float = 0.80

    # --- Ticket lifecycle ---
    ACK_TIMEOUT_MINUTES: int = 10
    MAX_AUTO_REASSIGN: int = 2
    MAX_ATTACHMENT_MB: int = 10
    AUTO_CLOSE_DAYS: int = 3
    REOPEN_WINDOW_DAYS: int = 14

    # --- Operations ---
    BACKUP_RETENTION_DAYS: int = 30


settings = Settings()  # type: ignore[call-arg]  # JWT_SECRET from env
