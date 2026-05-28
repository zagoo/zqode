from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.ids import quota_balance_id, quota_period_id, quota_policy_id
from app.models.base import Base, TimestampMixin


class QuotaResetPolicy(Base, TimestampMixin):
    __tablename__ = "quota_reset_policies"

    policy_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=quota_policy_id)
    reset_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="MONTHLY")
    reset_day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=1)
    reset_time: Mapped[Optional[datetime]] = mapped_column(Time, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default="UTC")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class QuotaPeriod(Base):
    __tablename__ = "quota_periods"

    quota_period_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=quota_period_id)
    period_type: Mapped[str] = mapped_column(String(16), nullable=False)
    period_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_policy_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("quota_reset_policies.policy_id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuotaBalance(Base, TimestampMixin):
    __tablename__ = "quota_balances"
    __table_args__ = (UniqueConstraint("user_id", "quota_period_id", name="uq_user_period"),)

    quota_balance_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=quota_balance_id)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    quota_period_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("quota_periods.quota_period_id"), nullable=False, index=True
    )
    cost_limit_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    consumed_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False, default=Decimal("0"))
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    quota_status: Mapped[str] = mapped_column(String(16), nullable=False, default="AVAILABLE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
