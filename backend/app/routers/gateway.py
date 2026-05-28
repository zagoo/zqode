"""M04 — LLM Gateway Runtime API.

These endpoints sit outside the platform envelope: success returns provider-native
bodies so OpenAI/Anthropic clients keep working unchanged.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Body, Header, Path, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core import errors, security
from app.core.deps import DBSession
from app.core.ids import outbox_id, request_id
from app.models import (
    APIKey,
    CostRecord,
    EnterpriseOpenAPI,
    LLMProvider,
    Model,
    Role,
    TransactionalOutbox,
    UsageLog,
    User,
)
from app.services import providers as provider_svc
from app.services import quota as quota_svc

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/gateway", tags=["gateway"])


def _extract_api_key(authorization: str | None, x_api_key: str | None) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    if x_api_key:
        return x_api_key.strip()
    raise errors.api_key_invalid()


async def _authenticate_api_key(db, raw_secret: str) -> tuple[APIKey, User]:
    secret_hash = security.hash_api_key_secret(raw_secret)
    key = (
        await db.execute(
            select(APIKey).where(APIKey.api_key_secret_hash == secret_hash)
        )
    ).scalar_one_or_none()
    if not key:
        raise errors.api_key_invalid()
    if key.status == "DISABLED":
        raise errors.api_key_disabled()
    if key.status == "DELETED":
        raise errors.api_key_invalid()
    if security.as_utc(key.expires_at) < datetime.now(timezone.utc):
        raise errors.api_key_expired()

    user = (
        await db.execute(
            select(User)
            .where(User.user_id == key.owner_user_id)
            .options(selectinload(User.role).selectinload(Role.permissions))
        )
    ).scalar_one_or_none()
    if not user:
        raise errors.api_key_invalid()
    if user.account_status != "ENABLED":
        raise errors.user_disabled()
    return key, user


async def _resolve_openapi(
    db, openapi_id_value: str, full_path: str | None = None
) -> EnterpriseOpenAPI:
    o = (
        await db.execute(
            select(EnterpriseOpenAPI).where(
                EnterpriseOpenAPI.openapi_id == openapi_id_value
            )
        )
    ).scalar_one_or_none()
    if not o and full_path:
        # fallback: match by gateway_url so human-readable slugs work as real endpoints
        o = (
            await db.execute(
                select(EnterpriseOpenAPI).where(
                    EnterpriseOpenAPI.gateway_url == full_path
                )
            )
        ).scalar_one_or_none()
    if not o or o.status != "ACTIVE":
        raise errors.not_found("Gateway endpoint not configured.")
    return o


async def _resolve_model(db, model_name: str) -> Model:
    m = (
        (
            await db.execute(
                select(Model)
                .where(Model.model_name == model_name, Model.status == "ACTIVE")
                .options(selectinload(Model.provider))
            )
        )
        .scalars()
        .first()
    )
    if not m:
        raise errors.model_not_found()
    if not m.provider or m.provider.status != "ACTIVE":
        raise errors.provider_not_configured()
    return m


def _compute_costs(
    input_tokens: int, output_tokens: int, model: Model
) -> tuple[Decimal, Decimal, Decimal]:
    million = Decimal("1000000")
    inp = (Decimal(input_tokens) / million) * model.input_price_per_million_tokens
    out = (Decimal(output_tokens) / million) * model.output_price_per_million_tokens
    return (
        inp.quantize(Decimal("0.000001")),
        out.quantize(Decimal("0.000001")),
        (inp + out).quantize(Decimal("0.000001")),
    )


async def _process_gateway(
    db,
    openapi: EnterpriseOpenAPI,
    payload: dict[str, Any],
    raw_secret: str,
) -> dict[str, Any]:
    api_key, user = await _authenticate_api_key(db, raw_secret)
    model_name = payload.get("model")
    if not model_name or not isinstance(model_name, str):
        raise errors.validation_error("'model' field is required.")
    model = await _resolve_model(db, model_name)

    # quota precheck
    period = await quota_svc.resolve_current_period(db)
    bal = await quota_svc.get_or_create_balance(db, user, period)
    if bal.quota_status == "EXCEEDED" or bal.remaining_amount <= 0:
        raise errors.quota_exceeded()

    started = datetime.now(timezone.utc)
    gw_req_id = request_id()
    if openapi.api_type == "OPENAI_COMPATIBLE":
        prompt_text = provider_svc._flatten_prompt_openai(payload)
    else:
        prompt_text = provider_svc._flatten_prompt_anthropic(payload)

    usage_log = UsageLog(
        gateway_request_id=gw_req_id,
        trace_id=gw_req_id,
        api_key_id=api_key.api_key_id,
        api_key_mask=api_key.api_key_mask,
        user_id=user.user_id,
        enterprise_openapi_id=openapi.openapi_id,
        provider_id=model.provider_id,
        model_id=model.model_id,
        model_name_snapshot=model.model_name,
        request_started_at=started,
        request_status="PROVIDER_IN_FLIGHT",
        prompt_content=payload,
        created_at=started,
    )
    db.add(usage_log)
    await db.commit()

    try:
        if openapi.api_type == "OPENAI_COMPATIBLE":
            provider_response, http_status = await provider_svc.forward_openai(
                model.provider.api_base_url, model.provider.api_key_ciphertext, payload
            )
            input_tokens, output_tokens = provider_svc.extract_usage_openai(
                provider_response
            )
        else:
            provider_response, http_status = await provider_svc.forward_anthropic(
                model.provider.api_base_url, model.provider.api_key_ciphertext, payload
            )
            input_tokens, output_tokens = provider_svc.extract_usage_anthropic(
                provider_response
            )
    except Exception as exc:
        usage_log.request_status = "FAILED"
        usage_log.error_code = "PROVIDER_REQUEST_FAILED"
        usage_log.provider_completed_at = datetime.now(timezone.utc)
        await db.commit()
        raise errors.provider_request_failed(str(exc))

    completed = datetime.now(timezone.utc)
    if http_status >= 400 or input_tokens is None or output_tokens is None:
        usage_log.request_status = (
            "COST_FAILED"
            if (input_tokens is None or output_tokens is None)
            else "FAILED"
        )
        usage_log.error_code = (
            "TOKEN_USAGE_MISSING"
            if (input_tokens is None or output_tokens is None)
            else f"HTTP_{http_status}"
        )
        usage_log.response_content = provider_response
        usage_log.provider_completed_at = completed
        usage_log.latency_ms = int((completed - started).total_seconds() * 1000)
        await db.commit()
        if input_tokens is None or output_tokens is None:
            raise errors.token_usage_missing()
        raise errors.provider_request_failed(f"upstream status {http_status}")

    input_cost, output_cost, total_cost = _compute_costs(
        input_tokens, output_tokens, model
    )

    # transactional cost deduction + outbox
    usage_log.request_status = "SUCCESS"
    usage_log.response_content = provider_response
    usage_log.input_tokens = input_tokens
    usage_log.output_tokens = output_tokens
    usage_log.total_tokens = input_tokens + output_tokens
    usage_log.provider_completed_at = completed
    usage_log.latency_ms = int((completed - started).total_seconds() * 1000)

    cost = CostRecord(
        usage_log_id=usage_log.usage_log_id,
        user_id=user.user_id,
        api_key_id=api_key.api_key_id,
        model_id=model.model_id,
        quota_period_id=period.quota_period_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_unit_price_per_million=model.input_price_per_million_tokens,
        output_unit_price_per_million=model.output_price_per_million_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
        currency=model.currency,
        cost_calculation_status="CALCULATED",
        created_at=completed,
    )
    db.add(cost)

    await quota_svc.deduct(db, bal, total_cost)

    db.add(
        TransactionalOutbox(
            event_type="usage.log.persisted",
            aggregate_type="UsageLog",
            aggregate_id=usage_log.usage_log_id,
            payload={
                "usage_log_id": usage_log.usage_log_id,
                "user_id": user.user_id,
                "api_key_id": api_key.api_key_id,
                "model_id": model.model_id,
                "provider_id": model.provider_id,
                "quota_period_id": period.quota_period_id,
                "request_status": "SUCCESS",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "input_cost": str(input_cost),
                "output_cost": str(output_cost),
                "total_cost": str(total_cost),
                "currency": model.currency,
                "request_started_at": started.isoformat(),
            },
            next_attempt_at=completed,
            created_at=completed,
        )
    )

    await db.commit()
    return provider_response


@router.post(
    "/{openapi_id}/v1/chat/completions",
    operation_id="gateway_openai_chat_completions",
    summary="OpenAI-compatible chat completion gateway",
)
async def openai_chat_completions(
    openapi_id: Annotated[str, Path()],
    payload: Annotated[dict[str, Any], Body()],
    request: Request,
    db: DBSession,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
):
    raw = _extract_api_key(authorization, x_api_key)
    openapi = await _resolve_openapi(db, openapi_id, request.url.path)
    if openapi.api_type != "OPENAI_COMPATIBLE":
        raise errors.validation_error("Endpoint is not OpenAI-compatible.")
    return await _process_gateway(db, openapi, payload, raw)


@router.post(
    "/{openapi_id}/v1/messages",
    operation_id="gateway_anthropic_messages",
    summary="Anthropic-compatible messages gateway",
)
async def anthropic_messages(
    openapi_id: Annotated[str, Path()],
    payload: Annotated[dict[str, Any], Body()],
    request: Request,
    db: DBSession,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
):
    raw = _extract_api_key(authorization, x_api_key)
    openapi = await _resolve_openapi(db, openapi_id, request.url.path)
    if openapi.api_type != "ANTHROPIC_COMPATIBLE":
        raise errors.validation_error("Endpoint is not Anthropic-compatible.")
    return await _process_gateway(db, openapi, payload, raw)
