from typing import Annotated, AsyncGenerator

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import errors, security
from app.database import get_db
from app.models import Role, RolePermission, User


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DBSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise errors.auth_required()
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = security.decode_token(token)
    except Exception as exc:  # invalid signature/expired
        raise errors.invalid_session() from exc
    if payload.get("type") != "access":
        raise errors.invalid_session()
    user_id = payload.get("sub")
    if not user_id:
        raise errors.invalid_session()
    res = await db.execute(
        select(User).where(User.user_id == user_id).options(selectinload(User.role).selectinload(Role.permissions))
    )
    user = res.scalar_one_or_none()
    if not user:
        raise errors.invalid_session()
    if user.account_status != "ENABLED":
        raise errors.user_disabled()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def user_permissions(user: User) -> set[str]:
    return {rp.permission_action for rp in user.role.permissions}


def require_permission(*required: str):
    async def _dep(user: CurrentUser) -> User:
        granted = {rp.permission_action for rp in user.role.permissions}
        if not set(required).issubset(granted):
            raise errors.permission_denied(f"Missing permission: {required}")
        return user

    return _dep
