"""M05 — Data Analytics & Reporting (UsageLog + CostRecord as source of truth)."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DBSession, require_permission
from app.models import CostRecord, Model, UsageLog, User
from app.schemas.analytics import (
    ConsumptionDetailRow,
    ModelBreakdown,
    PersonalConsumption,
    PromptCategoryStat,
    RankingEntry,
    RankingResponse,
    SummaryRow,
    TrendPoint,
)
from app.schemas.response import ApiResponse, PageData, ok
from app.services import quota as quota_svc

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _period_bucket(d: datetime, granularity: str) -> str:
    if granularity == "DAY":
        return d.strftime("%Y-%m-%d")
    if granularity == "WEEK":
        iso = d.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return d.strftime("%Y-%m")


def _resolve_window(period_type: str, period_start: Optional[datetime], period_end: Optional[datetime]) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if period_start and period_end:
        return period_start, period_end
    if period_type == "DAY":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    if period_type == "WEEK":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = start.fromordinal(start.toordinal() - start.weekday())
        return start.replace(tzinfo=timezone.utc), now
    if period_type == "MONTH":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now
    # CURRENT_ACCUMULATED — current quota period
    return datetime(2000, 1, 1, tzinfo=timezone.utc), now


@router.get(
    "/personal-consumption",
    response_model=ApiResponse[PersonalConsumption],
    operation_id="analytics_personal_consumption",
)
async def personal_consumption(
    user: CurrentUser,
    db: DBSession,
    _: User = Depends(require_permission("analytics.personal.read")),
    period_type: str = Query("CURRENT_ACCUMULATED"),
    granularity: str = Query("DAY"),
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
):
    start, end = _resolve_window(period_type, period_start, period_end)

    logs_q = (
        select(UsageLog, CostRecord, Model.model_name)
        .join(CostRecord, CostRecord.usage_log_id == UsageLog.usage_log_id, isouter=True)
        .join(Model, Model.model_id == UsageLog.model_id, isouter=True)
        .where(
            UsageLog.user_id == user.user_id,
            UsageLog.request_status == "SUCCESS",
            UsageLog.request_started_at >= start,
            UsageLog.request_started_at <= end,
        )
    )
    rows = (await db.execute(logs_q)).all()

    total_in = total_out = 0
    total_cost = Decimal("0")
    currency = "USD"
    by_period: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"in": Decimal(0), "out": Decimal(0), "cost": Decimal(0)})
    by_model: dict[str, dict[str, Decimal | str]] = {}

    for ul, cr, model_name in rows:
        i = ul.input_tokens or 0
        o = ul.output_tokens or 0
        total_in += i
        total_out += o
        c = (cr.total_cost if cr else Decimal("0")) or Decimal("0")
        total_cost += c
        if cr:
            currency = cr.currency
        bucket = _period_bucket(ul.request_started_at, granularity)
        bp = by_period[bucket]
        bp["in"] += i
        bp["out"] += o
        bp["cost"] += c
        if ul.model_id:
            mb = by_model.setdefault(
                ul.model_id, {"name": model_name or ul.model_name_snapshot or "", "tokens": 0, "cost": Decimal("0")}
            )
            mb["tokens"] = int(mb["tokens"]) + i + o
            mb["cost"] = Decimal(mb["cost"]) + c

    period = await quota_svc.resolve_current_period(db)
    bal = await quota_svc.get_or_create_balance(db, user, period)
    limit = bal.cost_limit_amount or Decimal("0")
    consumed = bal.consumed_amount or Decimal("0")
    ratio = float(consumed / limit) if limit > 0 else 0.0

    trend = [
        TrendPoint(
            period=k,
            input_tokens=int(v["in"]),
            output_tokens=int(v["out"]),
            total_tokens=int(v["in"] + v["out"]),
            total_cost=v["cost"],
        )
        for k, v in sorted(by_period.items())
    ]

    model_breakdown = [
        ModelBreakdown(
            model_id=mid, model_name=str(v["name"]), total_tokens=int(v["tokens"]), total_cost=Decimal(v["cost"])
        )
        for mid, v in by_model.items()
    ]

    return ok(
        PersonalConsumption(
            total_input_tokens=total_in,
            total_output_tokens=total_out,
            total_tokens=total_in + total_out,
            total_cost=total_cost,
            currency=currency,
            current_period_consumed=consumed,
            current_period_limit=limit,
            quota_usage_ratio=ratio,
            trend=trend,
            by_model=model_breakdown,
        )
    )


@router.get(
    "/consumption-ranking",
    response_model=ApiResponse[RankingResponse],
    operation_id="analytics_consumption_ranking",
)
async def consumption_ranking(
    user: CurrentUser,
    db: DBSession,
    _: User = Depends(require_permission("analytics.ranking.read")),
    period_type: str = Query("CURRENT_ACCUMULATED"),
):
    start, end = _resolve_window(period_type, None, None)
    res = await db.execute(
        select(
            UsageLog.user_id,
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label("tokens"),
            func.coalesce(func.sum(CostRecord.total_cost), 0).label("cost"),
        )
        .join(CostRecord, CostRecord.usage_log_id == UsageLog.usage_log_id, isouter=True)
        .where(UsageLog.request_status == "SUCCESS", UsageLog.request_started_at >= start, UsageLog.request_started_at <= end)
        .group_by(UsageLog.user_id)
        .order_by(func.coalesce(func.sum(CostRecord.total_cost), 0).desc())
    )
    rows = res.all()
    total_users = len(rows)
    top_n = max(1, math.ceil(total_users * 0.30)) if total_users > 0 else 0

    entries: list[RankingEntry] = []
    anon_index = 1
    current_in_top = False
    for rank, (uid, tokens, cost) in enumerate(rows[:top_n], start=1):
        is_me = uid == user.user_id
        if is_me:
            current_in_top = True
        entries.append(
            RankingEntry(
                rank=rank,
                display_name="You" if is_me else f"Anonymous User {anon_index}",
                total_tokens=int(tokens or 0),
                total_cost=Decimal(cost or 0),
                is_current_user=is_me,
            )
        )
        if not is_me:
            anon_index += 1

    if not current_in_top:
        for rank, (uid, tokens, cost) in enumerate(rows, start=1):
            if uid == user.user_id:
                entries.append(
                    RankingEntry(
                        rank=rank,
                        display_name="You",
                        total_tokens=int(tokens or 0),
                        total_cost=Decimal(cost or 0),
                        is_current_user=True,
                    )
                )
                break

    return ok(RankingResponse(entries=entries, total_users=total_users))


@router.get(
    "/prompt-categories",
    response_model=ApiResponse[list[PromptCategoryStat]],
    operation_id="analytics_prompt_categories",
)
async def prompt_categories(
    user: CurrentUser,
    db: DBSession,
    _: User = Depends(require_permission("analytics.prompt_category.read")),
):
    # Prototype: classifier worker not wired; return empty list deterministically.
    return ok([])


@router.get(
    "/consumption-details",
    response_model=ApiResponse[PageData[ConsumptionDetailRow]],
    operation_id="analytics_consumption_details",
)
async def consumption_details(
    db: DBSession,
    _: User = Depends(require_permission("analytics.detail.read")),
    period_type: str = Query("CURRENT_ACCUMULATED"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    start, end = _resolve_window(period_type, None, None)
    res = await db.execute(
        select(UsageLog, CostRecord, User.enterprise_email)
        .join(CostRecord, CostRecord.usage_log_id == UsageLog.usage_log_id, isouter=True)
        .join(User, User.user_id == UsageLog.user_id, isouter=True)
        .where(UsageLog.request_started_at >= start, UsageLog.request_started_at <= end)
        .order_by(UsageLog.request_started_at.desc())
    )
    rows = res.all()
    items_all = [
        ConsumptionDetailRow(
            usage_log_id=ul.usage_log_id,
            time=ul.request_started_at,
            user_email=email or "",
            api_key_mask=ul.api_key_mask or "",
            model_name=ul.model_name_snapshot or "",
            input_tokens=ul.input_tokens or 0,
            output_tokens=ul.output_tokens or 0,
            cost=(cr.total_cost if cr else Decimal("0")),
            currency=(cr.currency if cr else "USD"),
            status=ul.request_status,
        )
        for ul, cr, email in rows
    ]
    total = len(items_all)
    items = items_all[(page - 1) * page_size : page * page_size]
    return ok(PageData(items=items, total=total, page=page, page_size=page_size))


@router.get(
    "/consumption-summary",
    response_model=ApiResponse[list[SummaryRow]],
    operation_id="analytics_consumption_summary",
)
async def consumption_summary(
    db: DBSession,
    _: User = Depends(require_permission("analytics.summary.read")),
    granularity: str = Query("DAY"),
    period_type: str = Query("CURRENT_ACCUMULATED"),
):
    start, end = _resolve_window(period_type, None, None)
    res = await db.execute(
        select(UsageLog, CostRecord)
        .join(CostRecord, CostRecord.usage_log_id == UsageLog.usage_log_id, isouter=True)
        .where(UsageLog.request_status == "SUCCESS", UsageLog.request_started_at >= start, UsageLog.request_started_at <= end)
    )
    buckets: dict[str, dict[str, Decimal | int | str]] = {}
    for ul, cr in res.all():
        b = _period_bucket(ul.request_started_at, granularity)
        row = buckets.setdefault(
            b,
            {"in": 0, "out": 0, "cost": Decimal("0"), "count": 0, "currency": "USD"},
        )
        row["in"] = int(row["in"]) + (ul.input_tokens or 0)
        row["out"] = int(row["out"]) + (ul.output_tokens or 0)
        row["count"] = int(row["count"]) + 1
        if cr:
            row["cost"] = Decimal(row["cost"]) + (cr.total_cost or Decimal("0"))
            row["currency"] = cr.currency
    out = [
        SummaryRow(
            period=k,
            total_input_tokens=int(v["in"]),
            total_output_tokens=int(v["out"]),
            total_tokens=int(v["in"]) + int(v["out"]),
            total_cost=Decimal(v["cost"]),
            currency=str(v["currency"]),
            request_count=int(v["count"]),
        )
        for k, v in sorted(buckets.items())
    ]
    return ok(out)
