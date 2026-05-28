from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://zqode:zqode_dev@postgres:5432/zqode"
    JWT_SECRET_KEY: str = "dev_change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    ALLOWED_EMAIL_DOMAINS: str = "example.com"
    INITIAL_ADMIN_ENTERPRISE_EMAIL: str = "admin@example.com"

    DEFAULT_CURRENCY: str = "USD"
    LOGIN_CHALLENGE_EXPIRE_MINUTES: int = 5
    LOGIN_CHALLENGE_MAX_ATTEMPTS: int = 5
    API_KEY_SECRET_TTL_SECONDS: int = 300

    # console = print code to stdout; smtp would dispatch real email
    EMAIL_MODE: str = "console"

    @property
    def allowed_domains(self) -> List[str]:
        return [d.strip().lower() for d in self.ALLOWED_EMAIL_DOMAINS.split(",") if d.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
