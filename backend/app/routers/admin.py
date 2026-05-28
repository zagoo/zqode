"""M02 — Platform Administration Console."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core import errors
from app.core.deps import DBSession, require_permission
from app.core.permissions import ALL_PERMISSIONS
from app.models import (
    APIKey,
    EnterpriseOpenAPI,
    LLMProvider,
    Model,
    PermissionAction,
    QuotaResetPolicy,
    Role,
    RolePermission,
    User,
)
from app.schemas.admin import (
    AdminAPIKeyExtend,
    AdminAPIKeyOut,
    ModelCreate,
    ModelOut,
    ModelUpdate,
    OpenAPICreate,
    OpenAPIOut,
    OpenAPIUpdate,
    ProviderCreate,
    ProviderOut,
    ProviderUpdate,
    QuotaPolicyOut,
    QuotaPolicyUpdate,
    RoleCreate,
    RoleOut,
    RoleUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.schemas.response import ApiResponse, PageData, ok

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:4]}...{secret[-4:]}"


def _provider_out(p: LLMProvider) -> ProviderOut:
    return ProviderOut(
        provider_id=p.provider_id,
        provider_name=p.provider_name,
        api_base_url=p.api_base_url,
        api_key_mask=p.api_key_mask,
        api_description=p.api_description,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
        version=p.version,
    )


def _model_out(m: Model) -> ModelOut:
    return ModelOut(
        model_id=m.model_id,
        provider_id=m.provider_id,
        provider_name=m.provider.provider_name if m.provider else "",
        model_name=m.model_name,
        input_price_per_million_tokens=m.input_price_per_million_tokens,
        output_price_per_million_tokens=m.output_price_per_million_tokens,
        currency=m.currency,
        status=m.status,
        created_at=m.created_at,
        updated_at=m.updated_at,
        version=m.version,
    )


def _openapi_out(o: EnterpriseOpenAPI) -> OpenAPIOut:
    return OpenAPIOut(
        openapi_id=o.openapi_id,
        api_name=o.api_name,
        api_type=o.api_type,
        gateway_url=o.gateway_url,
        usage_description=o.usage_description,
        status=o.status,
        created_at=o.created_at,
        updated_at=o.updated_at,
        version=o.version,
    )


def _user_out(u: User) -> UserOut:
    return UserOut(
        user_id=u.user_id,
        enterprise_email=u.enterprise_email,
        role_id=u.role_id,
        role_name=u.role.role_name if u.role else "",
        cost_limit_source=u.cost_limit_source,
        cost_limit_amount=u.effective_cost_limit(),
        account_status=u.account_status,
        created_at=u.created_at,
        updated_at=u.updated_at,
        version=u.version,
    )


def _role_out(r: Role) -> RoleOut:
    return RoleOut(
        role_id=r.role_id,
        role_name=r.role_name,
        permissions=sorted([p.permission_action for p in r.permissions]),
        default_cost_limit_amount=r.default_cost_limit_amount,
        api_key_validity_days=r.api_key_validity_days,
        created_at=r.created_at,
        updated_at=r.updated_at,
        version=r.version,
    )


# =================== Providers ===================
@router.get("/providers", response_model=ApiResponse[PageData[ProviderOut]], operation_id="admin_list_providers")
async def list_providers(
    db: DBSession,
    _: User = Depends(require_permission("platform.provider.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = select(LLMProvider).where(LLMProvider.status != "DELETED").order_by(LLMProvider.created_at.desc())
    res = await db.execute(q)
    items = [_provider_out(p) for p in res.scalars().all()]
    total = len(items)
    page_items = items[(page - 1) * page_size : page * page_size]
    return ok(PageData(items=page_items, total=total, page=page, page_size=page_size))


@router.post("/providers", response_model=ApiResponse[ProviderOut], status_code=status.HTTP_201_CREATED, operation_id="admin_create_provider")
async def create_provider(
    body: ProviderCreate,
    db: DBSession,
    _: User = Depends(require_permission("platform.provider.create")),
):
    p = LLMProvider(
        provider_name=body.provider_name,
        api_base_url=body.api_base_url,
        api_key_ciphertext=body.api_key,  # NOTE: prototype stores as-is; production should encrypt with KMS
        api_key_mask=_mask_secret(body.api_key),
        api_description=body.api_description,
    )
    db.add(p)
    try:
        await db.commit()
    except IntegrityError:
        raise errors.duplicate_resource("Provider name already exists.")
    await db.refresh(p)
    return ok(_provider_out(p))


@router.get("/providers/{provider_id}", response_model=ApiResponse[ProviderOut], operation_id="admin_get_provider")
async def get_provider(
    provider_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.provider.read")),
):
    p = (await db.execute(select(LLMProvider).where(LLMProvider.provider_id == provider_id))).scalar_one_or_none()
    if not p or p.status == "DELETED":
        raise errors.not_found()
    return ok(_provider_out(p))


@router.patch("/providers/{provider_id}", response_model=ApiResponse[ProviderOut], operation_id="admin_update_provider")
async def update_provider(
    provider_id: str,
    body: ProviderUpdate,
    db: DBSession,
    _: User = Depends(require_permission("platform.provider.update")),
):
    p = (await db.execute(select(LLMProvider).where(LLMProvider.provider_id == provider_id))).scalar_one_or_none()
    if not p or p.status == "DELETED":
        raise errors.not_found()
    if body.provider_name is not None:
        p.provider_name = body.provider_name
    if body.api_base_url is not None:
        p.api_base_url = body.api_base_url
    if body.api_key is not None:
        p.api_key_ciphertext = body.api_key
        p.api_key_mask = _mask_secret(body.api_key)
    if body.api_description is not None:
        p.api_description = body.api_description
    p.version += 1
    await db.commit()
    await db.refresh(p)
    return ok(_provider_out(p))


@router.delete("/providers/{provider_id}", response_model=ApiResponse[None], operation_id="admin_delete_provider")
async def delete_provider(
    provider_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.provider.delete")),
):
    p = (await db.execute(select(LLMProvider).where(LLMProvider.provider_id == provider_id))).scalar_one_or_none()
    if not p:
        raise errors.not_found()
    p.status = "DELETED"
    p.version += 1
    await db.commit()
    return ok()


# =================== Models ===================
@router.get("/models", response_model=ApiResponse[PageData[ModelOut]], operation_id="admin_list_models")
async def list_models(
    db: DBSession,
    _: User = Depends(require_permission("platform.model.read")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = (
        select(Model)
        .where(Model.status != "DELETED")
        .options(selectinload(Model.provider))
        .order_by(Model.created_at.desc())
    )
    res = await db.execute(q)
    items = [_model_out(m) for m in res.scalars().all()]
    total = len(items)
    page_items = items[(page - 1) * page_size : page * page_size]
    return ok(PageData(items=page_items, total=total, page=page, page_size=page_size))


@router.post("/models", response_model=ApiResponse[ModelOut], status_code=status.HTTP_201_CREATED, operation_id="admin_create_model")
async def create_model(
    body: ModelCreate,
    db: DBSession,
    _: User = Depends(require_permission("platform.model.create")),
):
    provider = (await db.execute(select(LLMProvider).where(LLMProvider.provider_id == body.provider_id))).scalar_one_or_none()
    if not provider or provider.status == "DELETED":
        raise errors.not_found("Provider not found.")
    m = Model(
        provider_id=body.provider_id,
        model_name=body.model_name,
        input_price_per_million_tokens=body.input_price_per_million_tokens,
        output_price_per_million_tokens=body.output_price_per_million_tokens,
        currency=body.currency,
    )
    db.add(m)
    try:
        await db.commit()
    except IntegrityError:
        raise errors.duplicate_resource("Model already exists for provider.")
    await db.refresh(m, attribute_names=["provider"])
    return ok(_model_out(m))


@router.get("/models/{model_id}", response_model=ApiResponse[ModelOut], operation_id="admin_get_model")
async def get_model(
    model_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.model.read")),
):
    m = (
        await db.execute(select(Model).where(Model.model_id == model_id).options(selectinload(Model.provider)))
    ).scalar_one_or_none()
    if not m or m.status == "DELETED":
        raise errors.not_found()
    return ok(_model_out(m))


@router.patch("/models/{model_id}", response_model=ApiResponse[ModelOut], operation_id="admin_update_model")
async def update_model(
    model_id: str,
    body: ModelUpdate,
    db: DBSession,
    _: User = Depends(require_permission("platform.model.update")),
):
    m = (
        await db.execute(select(Model).where(Model.model_id == model_id).options(selectinload(Model.provider)))
    ).scalar_one_or_none()
    if not m or m.status == "DELETED":
        raise errors.not_found()
    if body.model_name is not None:
        m.model_name = body.model_name
    if body.input_price_per_million_tokens is not None:
        m.input_price_per_million_tokens = body.input_price_per_million_tokens
    if body.output_price_per_million_tokens is not None:
        m.output_price_per_million_tokens = body.output_price_per_million_tokens
    if body.currency is not None:
        m.currency = body.currency
    m.version += 1
    await db.commit()
    await db.refresh(m, attribute_names=["provider"])
    return ok(_model_out(m))


@router.delete("/models/{model_id}", response_model=ApiResponse[None], operation_id="admin_delete_model")
async def delete_model(
    model_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.model.delete")),
):
    m = (await db.execute(select(Model).where(Model.model_id == model_id))).scalar_one_or_none()
    if not m:
        raise errors.not_found()
    m.status = "DELETED"
    m.version += 1
    await db.commit()
    return ok()


# =================== Enterprise OpenAPIs ===================
@router.get("/enterprise-openapis", response_model=ApiResponse[PageData[OpenAPIOut]], operation_id="admin_list_openapis")
async def list_openapis(
    db: DBSession,
    _: User = Depends(require_permission("platform.openapi.read")),
):
    res = await db.execute(
        select(EnterpriseOpenAPI).where(EnterpriseOpenAPI.status != "DELETED").order_by(EnterpriseOpenAPI.created_at.desc())
    )
    items = [_openapi_out(o) for o in res.scalars().all()]
    return ok(PageData(items=items, total=len(items), page=1, page_size=len(items) or 1))


@router.post("/enterprise-openapis", response_model=ApiResponse[OpenAPIOut], status_code=status.HTTP_201_CREATED, operation_id="admin_create_openapi")
async def create_openapi(
    body: OpenAPICreate,
    db: DBSession,
    _: User = Depends(require_permission("platform.openapi.create")),
):
    if body.api_type not in ("OPENAI_COMPATIBLE", "ANTHROPIC_COMPATIBLE"):
        raise errors.validation_error("api_type must be OPENAI_COMPATIBLE or ANTHROPIC_COMPATIBLE.")
    o = EnterpriseOpenAPI(
        api_name=body.api_name,
        api_type=body.api_type,
        gateway_url=body.gateway_url,
        usage_description=body.usage_description,
    )
    db.add(o)
    try:
        await db.commit()
    except IntegrityError:
        raise errors.duplicate_resource("Enterprise OpenAPI name or URL already exists.")
    await db.refresh(o)
    return ok(_openapi_out(o))


@router.get("/enterprise-openapis/{openapi_id}", response_model=ApiResponse[OpenAPIOut], operation_id="admin_get_openapi")
async def get_openapi(
    openapi_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.openapi.read")),
):
    o = (await db.execute(select(EnterpriseOpenAPI).where(EnterpriseOpenAPI.openapi_id == openapi_id))).scalar_one_or_none()
    if not o or o.status == "DELETED":
        raise errors.not_found()
    return ok(_openapi_out(o))


@router.patch("/enterprise-openapis/{openapi_id}", response_model=ApiResponse[OpenAPIOut], operation_id="admin_update_openapi")
async def update_openapi(
    openapi_id: str,
    body: OpenAPIUpdate,
    db: DBSession,
    _: User = Depends(require_permission("platform.openapi.update")),
):
    o = (await db.execute(select(EnterpriseOpenAPI).where(EnterpriseOpenAPI.openapi_id == openapi_id))).scalar_one_or_none()
    if not o or o.status == "DELETED":
        raise errors.not_found()
    if body.api_name is not None:
        o.api_name = body.api_name
    if body.api_type is not None:
        o.api_type = body.api_type
    if body.gateway_url is not None:
        o.gateway_url = body.gateway_url
    if body.usage_description is not None:
        o.usage_description = body.usage_description
    o.version += 1
    await db.commit()
    await db.refresh(o)
    return ok(_openapi_out(o))


@router.delete("/enterprise-openapis/{openapi_id}", response_model=ApiResponse[None], operation_id="admin_delete_openapi")
async def delete_openapi(
    openapi_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.openapi.delete")),
):
    o = (await db.execute(select(EnterpriseOpenAPI).where(EnterpriseOpenAPI.openapi_id == openapi_id))).scalar_one_or_none()
    if not o:
        raise errors.not_found()
    o.status = "DELETED"
    o.version += 1
    await db.commit()
    return ok()


# =================== Users ===================
@router.get("/users", response_model=ApiResponse[PageData[UserOut]], operation_id="admin_list_users")
async def list_users(
    db: DBSession,
    _: User = Depends(require_permission("platform.user.read")),
):
    res = await db.execute(
        select(User).where(User.deleted_at.is_(None)).options(selectinload(User.role)).order_by(User.created_at.desc())
    )
    items = [_user_out(u) for u in res.scalars().all()]
    return ok(PageData(items=items, total=len(items), page=1, page_size=len(items) or 1))


@router.post("/users", response_model=ApiResponse[UserOut], status_code=status.HTTP_201_CREATED, operation_id="admin_create_user")
async def create_user(
    body: UserCreate,
    db: DBSession,
    _: User = Depends(require_permission("platform.user.create")),
):
    email = body.enterprise_email.lower().strip()
    role = (await db.execute(select(Role).where(Role.role_id == body.role_id))).scalar_one_or_none()
    if not role:
        raise errors.not_found("Role not found.")
    if body.cost_limit_source == "USER_CUSTOM" and body.custom_cost_limit_amount is None:
        raise errors.validation_error("custom_cost_limit_amount required when cost_limit_source=USER_CUSTOM.")
    u = User(
        enterprise_email=email,
        role_id=body.role_id,
        cost_limit_source=body.cost_limit_source,
        custom_cost_limit_amount=body.custom_cost_limit_amount,
        account_status=body.account_status,
    )
    db.add(u)
    try:
        await db.commit()
    except IntegrityError:
        raise errors.duplicate_resource("Enterprise email already exists.")
    await db.refresh(u, attribute_names=["role"])
    return ok(_user_out(u))


@router.get("/users/{user_id}", response_model=ApiResponse[UserOut], operation_id="admin_get_user")
async def get_user(
    user_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.user.read")),
):
    u = (
        await db.execute(select(User).where(User.user_id == user_id).options(selectinload(User.role)))
    ).scalar_one_or_none()
    if not u or u.deleted_at is not None:
        raise errors.not_found()
    return ok(_user_out(u))


@router.patch("/users/{user_id}", response_model=ApiResponse[UserOut], operation_id="admin_update_user")
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: DBSession,
    _: User = Depends(require_permission("platform.user.update")),
):
    u = (
        await db.execute(select(User).where(User.user_id == user_id).options(selectinload(User.role)))
    ).scalar_one_or_none()
    if not u or u.deleted_at is not None:
        raise errors.not_found()
    if body.role_id is not None:
        r = (await db.execute(select(Role).where(Role.role_id == body.role_id))).scalar_one_or_none()
        if not r:
            raise errors.not_found("Role not found.")
        u.role_id = body.role_id
    if body.cost_limit_source is not None:
        u.cost_limit_source = body.cost_limit_source
    if body.custom_cost_limit_amount is not None:
        u.custom_cost_limit_amount = body.custom_cost_limit_amount
    if body.account_status is not None:
        u.account_status = body.account_status
    u.version += 1
    await db.commit()
    await db.refresh(u, attribute_names=["role"])
    return ok(_user_out(u))


@router.delete("/users/{user_id}", response_model=ApiResponse[None], operation_id="admin_delete_user")
async def delete_user(
    user_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.user.delete")),
):
    u = (await db.execute(select(User).where(User.user_id == user_id))).scalar_one_or_none()
    if not u:
        raise errors.not_found()
    u.account_status = "DISABLED"
    u.deleted_at = datetime.now(timezone.utc)
    u.version += 1
    await db.commit()
    return ok()


# =================== Roles ===================
@router.get("/roles", response_model=ApiResponse[PageData[RoleOut]], operation_id="admin_list_roles")
async def list_roles(
    db: DBSession,
    _: User = Depends(require_permission("platform.role.read")),
):
    res = await db.execute(
        select(Role).where(Role.status != "DELETED").options(selectinload(Role.permissions)).order_by(Role.created_at)
    )
    items = [_role_out(r) for r in res.scalars().all()]
    return ok(PageData(items=items, total=len(items), page=1, page_size=len(items) or 1))


@router.get("/roles/available-permissions", response_model=ApiResponse[List[str]], operation_id="admin_list_permission_actions")
async def list_permission_actions(
    db: DBSession,
    _: User = Depends(require_permission("platform.role.read")),
):
    res = await db.execute(select(PermissionAction).order_by(PermissionAction.permission_action))
    return ok([p.permission_action for p in res.scalars().all()])


@router.post("/roles", response_model=ApiResponse[RoleOut], status_code=status.HTTP_201_CREATED, operation_id="admin_create_role")
async def create_role(
    body: RoleCreate,
    db: DBSession,
    _: User = Depends(require_permission("platform.role.create")),
):
    valid = {p for p, _ in ALL_PERMISSIONS}
    invalid = set(body.permissions) - valid
    if invalid:
        raise errors.validation_error(f"Unknown permissions: {sorted(invalid)}")
    r = Role(
        role_name=body.role_name,
        default_cost_limit_amount=body.default_cost_limit_amount,
        api_key_validity_days=body.api_key_validity_days,
    )
    db.add(r)
    try:
        await db.flush()
    except IntegrityError:
        raise errors.duplicate_resource("Role name already exists.")
    for action in body.permissions:
        db.add(RolePermission(role_id=r.role_id, permission_action=action))
    await db.commit()
    await db.refresh(r, attribute_names=["permissions"])
    return ok(_role_out(r))


@router.get("/roles/{role_id}", response_model=ApiResponse[RoleOut], operation_id="admin_get_role")
async def get_role(
    role_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.role.read")),
):
    r = (
        await db.execute(select(Role).where(Role.role_id == role_id).options(selectinload(Role.permissions)))
    ).scalar_one_or_none()
    if not r or r.status == "DELETED":
        raise errors.not_found()
    return ok(_role_out(r))


@router.patch("/roles/{role_id}", response_model=ApiResponse[RoleOut], operation_id="admin_update_role")
async def update_role(
    role_id: str,
    body: RoleUpdate,
    db: DBSession,
    _: User = Depends(require_permission("platform.role.update")),
):
    r = (
        await db.execute(select(Role).where(Role.role_id == role_id).options(selectinload(Role.permissions)))
    ).scalar_one_or_none()
    if not r or r.status == "DELETED":
        raise errors.not_found()
    if body.role_name is not None:
        r.role_name = body.role_name
    if body.default_cost_limit_amount is not None:
        r.default_cost_limit_amount = body.default_cost_limit_amount
    if body.api_key_validity_days is not None:
        r.api_key_validity_days = body.api_key_validity_days
    if body.permissions is not None:
        valid = {p for p, _ in ALL_PERMISSIONS}
        invalid = set(body.permissions) - valid
        if invalid:
            raise errors.validation_error(f"Unknown permissions: {sorted(invalid)}")
        # replace
        for rp in list(r.permissions):
            await db.delete(rp)
        await db.flush()
        for action in body.permissions:
            db.add(RolePermission(role_id=r.role_id, permission_action=action))
    r.version += 1
    await db.commit()
    await db.refresh(r, attribute_names=["permissions"])
    return ok(_role_out(r))


@router.delete("/roles/{role_id}", response_model=ApiResponse[None], operation_id="admin_delete_role")
async def delete_role(
    role_id: str,
    db: DBSession,
    _: User = Depends(require_permission("platform.role.delete")),
):
    r = (await db.execute(select(Role).where(Role.role_id == role_id))).scalar_one_or_none()
    if not r:
        raise errors.not_found()
    in_use = (await db.execute(select(User).where(User.role_id == role_id, User.deleted_at.is_(None)))).first()
    if in_use:
        raise errors.duplicate_resource("Role has users assigned; reassign before deletion.")
    r.status = "DELETED"
    r.version += 1
    await db.commit()
    return ok()


# =================== API Keys (admin view) ===================
@router.get("/api-keys", response_model=ApiResponse[PageData[AdminAPIKeyOut]], operation_id="admin_list_api_keys")
async def list_api_keys(
    db: DBSession,
    _: User = Depends(require_permission("platform.api_key.read_all")),
):
    res = await db.execute(
        select(APIKey, User.enterprise_email)
        .join(User, User.user_id == APIKey.owner_user_id)
        .where(APIKey.status != "DELETED")
        .order_by(APIKey.created_at.desc())
    )
    rows = res.all()
    items = [
        AdminAPIKeyOut(
            api_key_id=k.api_key_id,
            owner_user_id=k.owner_user_id,
            owner_enterprise_email=email,
            key_name=k.key_name,
            api_key_mask=k.api_key_mask,
            application_date=k.application_date,
            expires_at=k.expires_at,
            status=k.status,
            created_at=k.created_at,
            updated_at=k.updated_at,
            version=k.version,
        )
        for (k, email) in rows
    ]
    return ok(PageData(items=items, total=len(items), page=1, page_size=len(items) or 1))


@router.patch("/api-keys/{api_key_id}/expiry", response_model=ApiResponse[AdminAPIKeyOut], operation_id="admin_extend_api_key_expiry")
async def extend_api_key_expiry(
    api_key_id: str,
    body: AdminAPIKeyExtend,
    db: DBSession,
    _: User = Depends(require_permission("platform.api_key.extend_expiry")),
):
    from app.core.security import as_utc
    k = (await db.execute(select(APIKey).where(APIKey.api_key_id == api_key_id))).scalar_one_or_none()
    if not k:
        raise errors.not_found()
    new_exp = as_utc(body.new_expires_at)
    if new_exp <= as_utc(k.expires_at):
        raise errors.validation_error("New expiry must be later than current expiry.")
    k.expires_at = new_exp
    k.version += 1
    await db.commit()
    owner_email = (await db.execute(select(User.enterprise_email).where(User.user_id == k.owner_user_id))).scalar_one()
    return ok(
        AdminAPIKeyOut(
            api_key_id=k.api_key_id,
            owner_user_id=k.owner_user_id,
            owner_enterprise_email=owner_email,
            key_name=k.key_name,
            api_key_mask=k.api_key_mask,
            application_date=k.application_date,
            expires_at=k.expires_at,
            status=k.status,
            created_at=k.created_at,
            updated_at=k.updated_at,
            version=k.version,
        )
    )


# =================== Quota Reset Policy ===================
@router.get("/quota-reset-policy", response_model=ApiResponse[QuotaPolicyOut], operation_id="admin_get_quota_policy")
async def get_quota_policy(
    db: DBSession,
    _: User = Depends(require_permission("platform.quota_policy.read")),
):
    p = (await db.execute(select(QuotaResetPolicy).limit(1))).scalar_one_or_none()
    if not p:
        p = QuotaResetPolicy(reset_mode="MONTHLY", reset_day_of_month=1, timezone="UTC")
        db.add(p)
        await db.commit()
        await db.refresh(p)
    return ok(
        QuotaPolicyOut(
            policy_id=p.policy_id,
            reset_mode=p.reset_mode,
            reset_day_of_month=p.reset_day_of_month,
            reset_time=p.reset_time,
            timezone=p.timezone,
            created_at=p.created_at,
            updated_at=p.updated_at,
            version=p.version,
        )
    )


@router.put("/quota-reset-policy", response_model=ApiResponse[QuotaPolicyOut], operation_id="admin_update_quota_policy")
async def update_quota_policy(
    body: QuotaPolicyUpdate,
    db: DBSession,
    _: User = Depends(require_permission("platform.quota_policy.update")),
):
    if body.reset_mode not in ("MONTHLY", "NONE"):
        raise errors.validation_error("reset_mode must be MONTHLY or NONE.")
    p = (await db.execute(select(QuotaResetPolicy).limit(1))).scalar_one_or_none()
    if not p:
        p = QuotaResetPolicy()
        db.add(p)
    p.reset_mode = body.reset_mode
    p.reset_day_of_month = body.reset_day_of_month if body.reset_mode == "MONTHLY" else None
    p.reset_time = body.reset_time
    p.timezone = body.timezone
    p.version += 1
    await db.commit()
    await db.refresh(p)
    return ok(
        QuotaPolicyOut(
            policy_id=p.policy_id,
            reset_mode=p.reset_mode,
            reset_day_of_month=p.reset_day_of_month,
            reset_time=p.reset_time,
            timezone=p.timezone,
            created_at=p.created_at,
            updated_at=p.updated_at,
            version=p.version,
        )
    )
