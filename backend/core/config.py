import secrets
from typing import Any, List, Literal, Optional

from pydantic import (
    AnyHttpUrl,
    EmailStr,
    PostgresDsn,
    ValidationInfo,
    computed_field,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)

    PROJECT_NAME: str
    FIREBASE_CRED: dict = {}
    SHEET_ID: str

    DOMAIN: str = "localhost"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    @computed_field  # type: ignore[misc]
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        if self.ENVIRONMENT == "local":
            return f"http://{self.DOMAIN}"
        return f"https://{self.DOMAIN}"

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    STORAGE_BUCKET: str = "bucket"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
