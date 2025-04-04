from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import RedisDsn  # Import RedisDsn for validation


class Settings(BaseSettings):
    # Configure Pydantic to load from the .env file in the project root
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields if any
    )

    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Database settings
    DATABASE_URL: str  # Basic string validation is often enough for SQLAlchemy

    # Redis settings (for arq task queue)
    REDIS_URL: RedisDsn  # Use Pydantic's RedisDsn for validation


settings = Settings()  # type: ignore
