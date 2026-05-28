from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import cost_record_id, usage_log_id
from app.models.base import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"

    usage_log_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=usage_log_id)
    gateway_request_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    trace_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    api_key_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("api_keys.api_key_id"), nullable=True)
    api_key_mask: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("users.user_id"), nullable=True, index=True
    )
    enterprise_openapi_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    provider_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    model_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("models.model_id"), nullable=True, index=True)
    model_name_snapshot: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    request_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    provider_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    request_status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROVIDER_IN_FLIGHT")
    prompt_content: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    response_content: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CostRecord(Base):
    __tablename__ = "cost_records"

    cost_record_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=cost_record_id)
    usage_log_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("usage_logs.usage_log_id"), unique=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    api_key_id: Mapped[str] = mapped_column(String(64), ForeignKey("api_keys.api_key_id"), nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), ForeignKey("models.model_id"), nullable=False)
    quota_period_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    output_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False)
    input_unit_price_per_million: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    output_unit_price_per_million: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    input_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    output_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    cost_calculation_status: Mapped[str] = mapped_column(String(48), nullable=False, default="CALCULATED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
