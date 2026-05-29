"""M01 — Platform Authentication & Login."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core import errors, security
from app.core.config import settings
from app.core.deps import CurrentUser, DBSession
from app.core.ids import session_id as new_session_id
from app.models import LoginChallenge, PlatformSession, Role, User
from app.schemas.auth import (
    LoginChallengeRequest,
    LoginChallengeResponse,
    LoginSessionRequest,
    LoginSessionResponse,
    RefreshTokenRequest,
    UserContext,
)
from app.schemas.response import ApiResponse, ok
from app.services import email as email_svc

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def _user_context(user: User) -> UserContext:
    return UserContext(
        user_id=user.user_id,
        enterprise_email=user.enterprise_email,
        role_id=user.role_id,
        role_name=user.role.role_name,
        cost_limit_amount=user.effective_cost_limit(),
        cost_limit_source=user.cost_limit_source,
        account_status=user.account_status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        version=user.version,
    )


@router.post(
    "/login/challenges",
    response_model=ApiResponse[LoginChallengeResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="auth_create_login_challenge",
    summary="Create login challenge — sends one-time random password",
)
async def create_login_challenge(body: LoginChallengeRequest, db: DBSession) -> ApiResponse[LoginChallengeResponse]:
    email = body.enterprise_email.lower().strip()
    domain = email.split("@")[-1]
    if settings.allowed_domains and domain not in settings.allowed_domains:
        raise errors.validation_error("Use your enterprise email address.")

    user = (await db.execute(select(User).where(User.enterprise_email == email))).scalar_one_or_none()
    # Surface user_disabled here rather than leaking enumeration of existing accounts via missing/disabled differentiation.
    if user and user.account_status != "ENABLED":
        raise errors.user_disabled()

    password = security.generate_random_password(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_CHALLENGE_EXPIRE_MINUTES)
    challenge = LoginChallenge(
        enterprise_email=email,
        random_password_hash=security.hash_password(password),
        expires_at=expires_at,
    )
    db.add(challenge)
    # Deliver the code before committing: if delivery fails the challenge is
    # rolled back, so no orphaned PENDING row is left behind.
    await email_svc.send_login_code(email, password, settings.LOGIN_CHALLENGE_EXPIRE_MINUTES)
    await db.commit()
    await db.refresh(challenge)

    return ok(
        LoginChallengeResponse(
            challenge_id=challenge.challenge_id,
            enterprise_email_mask=_mask_email(email),
            expires_at=challenge.expires_at,
            dev_random_password=password if settings.EMAIL_MODE == "console" else None,
        )
    )


@router.post(
    "/login/sessions",
    response_model=ApiResponse[LoginSessionResponse],
    status_code=status.HTTP_201_CREATED,
    operation_id="auth_create_login_session",
    summary="Verify random password and create session",
)
async def create_login_session(body: LoginSessionRequest, db: DBSession) -> ApiResponse[LoginSessionResponse]:
    email = body.enterprise_email.lower().strip()
    challenge = (
        await db.execute(select(LoginChallenge).where(LoginChallenge.challenge_id == body.challenge_id).with_for_update())
    ).scalar_one_or_none()
    if not challenge or challenge.status != "PENDING":
        raise errors.invalid_login_challenge()
    if security.as_utc(challenge.expires_at) < datetime.now(timezone.utc):
        challenge.status = "EXPIRED"
        await db.commit()
        raise errors.invalid_login_challenge()
    if challenge.enterprise_email != email:
        raise errors.invalid_login_challenge()
    if not security.verify_password(body.random_password, challenge.random_password_hash):
        challenge.attempt_count += 1
        if challenge.attempt_count >= settings.LOGIN_CHALLENGE_MAX_ATTEMPTS:
            challenge.status = "LOCKED"
        await db.commit()
        raise errors.invalid_random_password()

    user_q = await db.execute(
        select(User).where(User.enterprise_email == email).options(selectinload(User.role).selectinload(Role.permissions))
    )
    user = user_q.scalar_one_or_none()
    if not user:
        raise errors.invalid_login_challenge()
    if user.account_status != "ENABLED":
        raise errors.user_disabled()

    challenge.status = "CONSUMED"
    challenge.consumed_at = datetime.now(timezone.utc)

    permissions = sorted({rp.permission_action for rp in user.role.permissions})
    sid = new_session_id()
    access = security.encode_access_token(user.user_id, user.role_id, permissions)
    refresh = security.encode_refresh_token(user.user_id, sid)

    now = datetime.now(timezone.utc)
    session = PlatformSession(
        session_id=sid,
        user_id=user.user_id,
        session_token_hash=security.hash_session_token(refresh),
        issued_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        last_seen_at=now,
    )
    db.add(session)
    await db.commit()

    return ok(
        LoginSessionResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=_user_context(user),
            permissions=permissions,
        )
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[LoginSessionResponse],
    operation_id="auth_refresh_token",
    summary="Exchange refresh token for new access token",
)
async def refresh_token(body: RefreshTokenRequest, db: DBSession) -> ApiResponse[LoginSessionResponse]:
    try:
        payload = security.decode_token(body.refresh_token)
    except Exception as exc:
        raise errors.invalid_session() from exc
    if payload.get("type") != "refresh":
        raise errors.invalid_session()
    sid = payload.get("sid")
    uid = payload.get("sub")
    if not sid or not uid:
        raise errors.invalid_session()

    sess = (
        await db.execute(select(PlatformSession).where(PlatformSession.session_id == sid))
    ).scalar_one_or_none()
    if not sess or sess.revoked_at is not None or security.as_utc(sess.expires_at) < datetime.now(timezone.utc):
        raise errors.invalid_session()
    if sess.session_token_hash != security.hash_session_token(body.refresh_token):
        raise errors.invalid_session()

    user = (
        await db.execute(
            select(User).where(User.user_id == uid).options(selectinload(User.role).selectinload(Role.permissions))
        )
    ).scalar_one_or_none()
    if not user or user.account_status != "ENABLED":
        raise errors.user_disabled()
    permissions = sorted({rp.permission_action for rp in user.role.permissions})
    access = security.encode_access_token(user.user_id, user.role_id, permissions)

    return ok(
        LoginSessionResponse(
            access_token=access,
            refresh_token=body.refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=_user_context(user),
            permissions=permissions,
        )
    )


@router.get(
    "/me",
    response_model=ApiResponse[LoginSessionResponse],
    operation_id="auth_get_me",
    summary="Get current user and permissions",
)
async def get_me(user: CurrentUser) -> ApiResponse[LoginSessionResponse]:
    permissions = sorted({rp.permission_action for rp in user.role.permissions})
    return ok(
        LoginSessionResponse(
            access_token="",
            refresh_token="",
            expires_in=0,
            user=_user_context(user),
            permissions=permissions,
        )
    )


@router.post(
    "/logout",
    response_model=ApiResponse[None],
    operation_id="auth_logout",
    summary="Revoke current session",
)
async def logout(user: CurrentUser, db: DBSession) -> ApiResponse[None]:
    # Revoke all active sessions for user; cheap and safe for prototype.
    res = await db.execute(select(PlatformSession).where(PlatformSession.user_id == user.user_id))
    for s in res.scalars().all():
        if s.revoked_at is None:
            s.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return ok()
