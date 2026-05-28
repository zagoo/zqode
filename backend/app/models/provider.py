from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import model_id, openapi_id, provider_id
from app.models.base import Base, TimestampMixin


class LLMProvider(Base, TimestampMixin):
    __tablename__ = "llm_providers"

    provider_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=provider_id)
    provider_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    api_base_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    api_key_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_mask: Mapped[str] = mapped_column(String(64), nullable=False)
    api_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    models: Mapped[list["Model"]] = relationship(back_populates="provider")


class Model(Base, TimestampMixin):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("provider_id", "model_name", name="uq_provider_model_name"),)

    model_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=model_id)
    provider_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("llm_providers.provider_id"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(256), nullable=False)
    input_price_per_million_tokens: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    output_price_per_million_tokens: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    provider: Mapped["LLMProvider"] = relationship(back_populates="models", lazy="joined")


class EnterpriseOpenAPI(Base, TimestampMixin):
    __tablename__ = "enterprise_openapis"

    openapi_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=openapi_id)
    api_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    api_type: Mapped[str] = mapped_column(String(32), nullable=False)
    gateway_url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    usage_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
