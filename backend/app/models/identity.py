from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import (
    challenge_id,
    role_id,
    session_id,
    user_id,
)
from app.models.base import Base, TimestampMixin


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=role_id)
    role_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    default_cost_limit_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 6), nullable=False, default=Decimal("100.000000")
    )
    api_key_validity_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", cascade="all, delete-orphan", lazy="selectin"
    )
    users: Mapped[list["User"]] = relationship(back_populates="role")


class PermissionAction(Base):
    __tablename__ = "permission_actions"

    permission_action: Mapped[str] = mapped_column(String(128), primary_key=True)
    module_id: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    is_system_defined: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: __import__("datetime").datetime.utcnow(), nullable=False
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True
    )
    permission_action: Mapped[str] = mapped_column(
        String(128), ForeignKey("permission_actions.permission_action"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: __import__("datetime").datetime.utcnow(), nullable=False
    )

    role: Mapped["Role"] = relationship(back_populates="permissions")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=user_id)
    enterprise_email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    role_id: Mapped[str] = mapped_column(String(64), ForeignKey("roles.role_id"), nullable=False)
    cost_limit_source: Mapped[str] = mapped_column(String(16), nullable=False, default="ROLE_DEFAULT")
    custom_cost_limit_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 6), nullable=True)
    account_status: Mapped[str] = mapped_column(String(16), nullable=False, default="ENABLED")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    role: Mapped["Role"] = relationship(back_populates="users", lazy="joined")

    def effective_cost_limit(self) -> Decimal:
        if self.cost_limit_source == "USER_CUSTOM" and self.custom_cost_limit_amount is not None:
            return self.custom_cost_limit_amount
        return self.role.default_cost_limit_amount


class LoginChallenge(Base):
    __tablename__ = "login_challenges"

    challenge_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=challenge_id)
    enterprise_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    random_password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: __import__("datetime").datetime.utcnow(), nullable=False
    )


class PlatformSession(Base):
    __tablename__ = "platform_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=session_id)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    session_token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
