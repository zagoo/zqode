"""M00 — Idempotently seed permissions, default roles, and the initial System Administrator."""
import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.permissions import (
    ALL_PERMISSIONS,
    normal_user_permissions,
    system_administrator_permissions,
    team_manager_permissions,
)
from app.database import AsyncSessionLocal
from app.models import PermissionAction, Role, RolePermission, User

log = logging.getLogger(__name__)


SYS_ADMIN_ROLE = "System Administrator"
TEAM_MGR_ROLE = "Team Manager"
NORMAL_USER_ROLE = "Normal User"


async def _seed_permissions(session: AsyncSession) -> None:
    existing = {p.permission_action for p in (await session.execute(select(PermissionAction))).scalars().all()}
    for action, module_id in ALL_PERMISSIONS:
        if action not in existing:
            session.add(
                PermissionAction(
                    permission_action=action,
                    module_id=module_id,
                    description=action,
                    is_system_defined=True,
                )
            )
    await session.flush()


async def _ensure_role(session: AsyncSession, name: str, perms: list[str], default_limit: Decimal, validity_days: int) -> Role:
    existing = (await session.execute(select(Role).where(Role.role_name == name))).scalar_one_or_none()
    if existing:
        return existing
    role = Role(
        role_name=name,
        default_cost_limit_amount=default_limit,
        api_key_validity_days=validity_days,
    )
    session.add(role)
    await session.flush()
    for action in perms:
        session.add(RolePermission(role_id=role.role_id, permission_action=action))
    await session.flush()
    return role


async def _ensure_admin_user(session: AsyncSession, role: Role) -> None:
    email = (settings.INITIAL_ADMIN_ENTERPRISE_EMAIL or "").lower().strip()
    if not email:
        log.warning("INITIAL_ADMIN_ENTERPRISE_EMAIL is empty; skipping admin bootstrap")
        return
    domain = email.split("@")[-1] if "@" in email else ""
    if settings.allowed_domains and domain not in settings.allowed_domains:
        log.warning("Initial admin domain %s not in ALLOWED_EMAIL_DOMAINS", domain)
        return
    existing = (await session.execute(select(User).where(User.enterprise_email == email))).scalar_one_or_none()
    if existing:
        return
    session.add(User(enterprise_email=email, role_id=role.role_id, account_status="ENABLED"))
    await session.flush()


async def run_bootstrap() -> None:
    async with AsyncSessionLocal() as session:
        await _seed_permissions(session)
        sys_admin = await _ensure_role(
            session, SYS_ADMIN_ROLE, system_administrator_permissions(), Decimal("100000.000000"), 365
        )
        await _ensure_role(
            session, TEAM_MGR_ROLE, team_manager_permissions(), Decimal("500.000000"), 180
        )
        await _ensure_role(
            session, NORMAL_USER_ROLE, normal_user_permissions(), Decimal("100.000000"), 90
        )
        await _ensure_admin_user(session, sys_admin)
        await session.commit()
        log.info("core.bootstrap.complete")
