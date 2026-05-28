from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import api_key_id
from app.models.base import Base, TimestampMixin


class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    api_key_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=api_key_id)
    owner_user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.user_id"), nullable=False, index=True
    )
    key_name: Mapped[str] = mapped_column(String(128), nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    api_key_secret_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    api_key_mask: Mapped[str] = mapped_column(String(64), nullable=False)
    application_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ENABLED")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class APIKeySecretCache(Base):
    """Short-lived plain-text store so an Idempotency-Key retry can return the same raw secret."""
    __tablename__ = "api_key_secret_cache"

    idempotency_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    api_key_id: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_one_time_secret: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
