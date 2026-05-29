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

    ALLOWED_EMAIL_DOMAINS: str = "engineai.com.cn"
    INITIAL_ADMIN_ENTERPRISE_EMAIL: str = "rensb@engineai.com.cn"

    DEFAULT_CURRENCY: str = "USD"
    LOGIN_CHALLENGE_EXPIRE_MINUTES: int = 5
    LOGIN_CHALLENGE_MAX_ATTEMPTS: int = 5
    API_KEY_SECRET_TTL_SECONDS: int = 300

    # console = log the code to the backend logs (dev); smtp = deliver via email
    EMAIL_MODE: str = "console"

    # SMTP delivery — used when EMAIL_MODE=smtp
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_FROM_NAME: str = "ZQode Gateway"
    SMTP_STARTTLS: bool = True
    SMTP_SSL: bool = False
    SMTP_TIMEOUT_SECONDS: int = 15

    @property
    def allowed_domains(self) -> List[str]:
        return [
            d.strip().lower()
            for d in self.ALLOWED_EMAIL_DOMAINS.split(",")
            if d.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
