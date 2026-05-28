"""M03 — Workbench / Developer Portal."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core import errors, security
from app.core.config import settings
from app.core.deps import CurrentUser, DBSession, require_permission
from app.models import APIKey, EnterpriseOpenAPI, Model, User
from app.schemas.response import ApiResponse, PageData, ok
from app.schemas.workbench import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyOut,
    APIKeyStatusUpdate,
    WorkbenchModelOut,
    WorkbenchOpenAPIOut,
)

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


def _api_key_out(k: APIKey) -> APIKeyOut:
    return APIKeyOut(
        api_key_id=k.api_key_id,
        owner_user_id=k.owner_user_id,
        key_name=k.key_name,
        api_key_mask=k.api_key_mask,
        application_date=k.application_date,
        expires_at=k.expires_at,
        status=k.status,
        created_at=k.created_at,
        updated_at=k.updated_at,
        version=k.version,
    )


@router.post(
    "/api-keys",
    response_model=ApiResponse[APIKeyCreateResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="workbench_create_api_key",
)
async def create_api_key(
    body: APIKeyCreate,
    user: CurrentUser,
    db: DBSession,
    _: User = Depends(require_permission("workbench.api_key.create")),
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ApiResponse[APIKeyCreateResponse]:
    # Validate expiry against Role validity days
    max_days = user.role.api_key_validity_days
    desired = security.as_utc(body.expires_at)
    delta_days = (desired - datetime.now(timezone.utc)).days
    if delta_days > max_days:
        raise errors.api_key_validity_exceeded()
    if delta_days < 0:
        raise errors.validation_error("expires_at must be in the future.")

    raw, prefix, mask = security.generate_api_key_secret()
    k = APIKey(
        owner_user_id=user.user_id,
        key_name=body.key_name,
        api_key_prefix=prefix,
        api_key_secret_hash=security.hash_api_key_secret(raw),
        api_key_mask=mask,
        application_date=datetime.now(timezone.utc),
        expires_at=desired,
        status="ENABLED",
    )
    db.add(k)
    await db.commit()
    await db.refresh(k)
    return ok(
        APIKeyCreateResponse(
            api_key=_api_key_out(k),
            api_key_secret=raw,
            api_key_secret_available=True,
        )
    )


@router.get("/api-keys", response_model=ApiResponse[PageData[APIKeyOut]], operation_id="workbench_list_api_keys")
async def list_api_keys(
    user: CurrentUser,
    db: DBSession,
    _: User = Depends(require_permission("workbench.api_key.read_own")),
):
    res = await db.execute(
        select(APIKey)
        .where(APIKey.owner_user_id == user.user_id, APIKey.status != "DELETED")
        .order_by(APIKey.created_at.desc())
    )
    items = [_api_key_out(k) for k in res.scalars().all()]
    return ok(PageData(items=items, total=len(items), page=1, page_size=len(items) or 1))


@router.patch(
    "/api-keys/{api_key_id}/status",
    response_model=ApiResponse[APIKeyOut],
    operation_id="workbench_update_api_key_status",
)
async def update_api_key_status(
    api_key_id: str,
    body: APIKeyStatusUpdate,
    user: CurrentUser,
    db: DBSession,
    _: User = Depends(require_permission("workbench.api_key.update_status_own")),
):
    if body.status not in ("ENABLED", "DISABLED"):
        raise errors.validation_error("status must be ENABLED or DISABLED.")
    k = (await db.execute(select(APIKey).where(APIKey.api_key_id == api_key_id))).scalar_one_or_none()
    if not k:
        raise errors.not_found()
    if k.owner_user_id != user.user_id:
        raise errors.api_key_ownership_violation()
    if k.status == "DELETED":
        raise errors.validation_error("Cannot reactivate a deleted key.")
    k.status = body.status
    k.version += 1
    await db.commit()
    await db.refresh(k)
    return ok(_api_key_out(k))


@router.delete("/api-keys/{api_key_id}", response_model=ApiResponse[None], operation_id="workbench_delete_api_key")
async def delete_api_key(
    api_key_id: str,
    user: CurrentUser,
    db: DBSession,
    _: User = Depends(require_permission("workbench.api_key.delete_own")),
):
    k = (await db.execute(select(APIKey).where(APIKey.api_key_id == api_key_id))).scalar_one_or_none()
    if not k:
        raise errors.not_found()
    if k.owner_user_id != user.user_id:
        raise errors.api_key_ownership_violation()
    k.status = "DELETED"
    k.deleted_at = datetime.now(timezone.utc)
    k.version += 1
    await db.commit()
    return ok()


@router.get("/models", response_model=ApiResponse[PageData[WorkbenchModelOut]], operation_id="workbench_list_models")
async def list_models(
    db: DBSession,
    _: User = Depends(require_permission("workbench.model.read")),
):
    res = await db.execute(
        select(Model).where(Model.status == "ACTIVE").options(selectinload(Model.provider)).order_by(Model.model_name)
    )
    items = [
        WorkbenchModelOut(
            model_id=m.model_id,
            provider_id=m.provider_id,
            provider_name=m.provider.provider_name,
            model_name=m.model_name,
            input_price_per_million_tokens=m.input_price_per_million_tokens,
            output_price_per_million_tokens=m.output_price_per_million_tokens,
            currency=m.currency,
        )
        for m in res.scalars().all()
    ]
    return ok(PageData(items=items, total=len(items), page=1, page_size=len(items) or 1))


@router.get(
    "/enterprise-openapis",
    response_model=ApiResponse[PageData[WorkbenchOpenAPIOut]],
    operation_id="workbench_list_openapis",
)
async def list_openapis(
    db: DBSession,
    _: User = Depends(require_permission("workbench.openapi.read")),
):
    res = await db.execute(
        select(EnterpriseOpenAPI).where(EnterpriseOpenAPI.status == "ACTIVE").order_by(EnterpriseOpenAPI.api_name)
    )
    items = [
        WorkbenchOpenAPIOut(
            openapi_id=o.openapi_id,
            api_name=o.api_name,
            api_type=o.api_type,
            gateway_url=o.gateway_url,
            usage_description=o.usage_description,
        )
        for o in res.scalars().all()
    ]
    return ok(PageData(items=items, total=len(items), page=1, page_size=len(items) or 1))
