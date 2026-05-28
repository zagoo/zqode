"""Quota period resolution and balance ops."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QuotaBalance, QuotaPeriod, QuotaResetPolicy, User


def _month_start(d: datetime) -> datetime:
    return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_end(d: datetime) -> datetime:
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return d.replace(month=d.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


async def resolve_current_period(db: AsyncSession) -> QuotaPeriod:
    policy = (await db.execute(select(QuotaResetPolicy).limit(1))).scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if policy and policy.reset_mode == "NONE":
        start = datetime(2000, 1, 1, tzinfo=timezone.utc)
        period = (
            await db.execute(select(QuotaPeriod).where(QuotaPeriod.period_type == "NONE"))
        ).scalar_one_or_none()
        if not period:
            period = QuotaPeriod(period_type="NONE", period_start_at=start, period_end_at=None, created_at=now)
            db.add(period)
            await db.flush()
        return period

    start = _month_start(now)
    end = _month_end(now)
    period = (
        await db.execute(
            select(QuotaPeriod).where(
                QuotaPeriod.period_type == "MONTHLY",
                QuotaPeriod.period_start_at == start,
            )
        )
    ).scalar_one_or_none()
    if not period:
        period = QuotaPeriod(period_type="MONTHLY", period_start_at=start, period_end_at=end, created_at=now)
        db.add(period)
        await db.flush()
    return period


async def get_or_create_balance(db: AsyncSession, user: User, period: QuotaPeriod) -> QuotaBalance:
    bal = (
        await db.execute(
            select(QuotaBalance)
            .where(QuotaBalance.user_id == user.user_id, QuotaBalance.quota_period_id == period.quota_period_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if bal:
        return bal
    limit = user.effective_cost_limit()
    bal = QuotaBalance(
        user_id=user.user_id,
        quota_period_id=period.quota_period_id,
        cost_limit_amount=limit,
        consumed_amount=Decimal("0"),
        remaining_amount=limit,
        currency="USD",
        quota_status="AVAILABLE",
    )
    db.add(bal)
    await db.flush()
    return bal


async def deduct(db: AsyncSession, bal: QuotaBalance, amount: Decimal) -> QuotaBalance:
    bal.consumed_amount = (bal.consumed_amount or Decimal("0")) + amount
    bal.remaining_amount = bal.cost_limit_amount - bal.consumed_amount
    if bal.remaining_amount <= 0:
        bal.quota_status = "EXCEEDED"
    bal.version += 1
    return bal
