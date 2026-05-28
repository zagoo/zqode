"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-28 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(64), primary_key=True),
        sa.Column("role_name", sa.String(128), nullable=False, unique=True),
        sa.Column("default_cost_limit_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("api_key_validity_days", sa.Integer, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "permission_actions",
        sa.Column("permission_action", sa.String(128), primary_key=True),
        sa.Column("module_id", sa.String(16), nullable=False),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("is_system_defined", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.String(64), sa.ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
        sa.Column(
            "permission_action",
            sa.String(128),
            sa.ForeignKey("permission_actions.permission_action"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(64), primary_key=True),
        sa.Column("enterprise_email", sa.String(320), nullable=False, unique=True),
        sa.Column("role_id", sa.String(64), sa.ForeignKey("roles.role_id"), nullable=False),
        sa.Column("cost_limit_source", sa.String(16), nullable=False, server_default="ROLE_DEFAULT"),
        sa.Column("custom_cost_limit_amount", sa.Numeric(20, 6), nullable=True),
        sa.Column("account_status", sa.String(16), nullable=False, server_default="ENABLED"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "login_challenges",
        sa.Column("challenge_id", sa.String(64), primary_key=True),
        sa.Column("enterprise_email", sa.String(320), nullable=False),
        sa.Column("random_password_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_login_challenges_email", "login_challenges", ["enterprise_email"])
    op.create_table(
        "platform_sessions",
        sa.Column("session_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("session_token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_platform_sessions_user", "platform_sessions", ["user_id"])

    op.create_table(
        "llm_providers",
        sa.Column("provider_id", sa.String(64), primary_key=True),
        sa.Column("provider_name", sa.String(128), nullable=False, unique=True),
        sa.Column("api_base_url", sa.String(2048), nullable=False),
        sa.Column("api_key_ciphertext", sa.Text, nullable=False),
        sa.Column("api_key_mask", sa.String(64), nullable=False),
        sa.Column("api_description", sa.Text, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "models",
        sa.Column("model_id", sa.String(64), primary_key=True),
        sa.Column("provider_id", sa.String(64), sa.ForeignKey("llm_providers.provider_id"), nullable=False),
        sa.Column("model_name", sa.String(256), nullable=False),
        sa.Column("input_price_per_million_tokens", sa.Numeric(20, 6), nullable=False),
        sa.Column("output_price_per_million_tokens", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider_id", "model_name", name="uq_provider_model_name"),
    )
    op.create_index("ix_models_provider", "models", ["provider_id"])

    op.create_table(
        "enterprise_openapis",
        sa.Column("openapi_id", sa.String(64), primary_key=True),
        sa.Column("api_name", sa.String(128), nullable=False, unique=True),
        sa.Column("api_type", sa.String(32), nullable=False),
        sa.Column("gateway_url", sa.String(2048), nullable=False, unique=True),
        sa.Column("usage_description", sa.Text, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "api_keys",
        sa.Column("api_key_id", sa.String(64), primary_key=True),
        sa.Column("owner_user_id", sa.String(64), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("key_name", sa.String(128), nullable=False),
        sa.Column("api_key_prefix", sa.String(16), nullable=False),
        sa.Column("api_key_secret_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("api_key_mask", sa.String(64), nullable=False),
        sa.Column("application_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="ENABLED"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_api_keys_owner", "api_keys", ["owner_user_id"])
    op.create_index("ix_api_keys_prefix", "api_keys", ["api_key_prefix"])
    op.create_index("ix_api_keys_expires", "api_keys", ["expires_at"])

    op.create_table(
        "api_key_secret_cache",
        sa.Column("idempotency_key", sa.String(128), primary_key=True),
        sa.Column("api_key_id", sa.String(64), nullable=False),
        sa.Column("encrypted_one_time_secret", sa.Text, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "quota_reset_policies",
        sa.Column("policy_id", sa.String(64), primary_key=True),
        sa.Column("reset_mode", sa.String(16), nullable=False, server_default="MONTHLY"),
        sa.Column("reset_day_of_month", sa.Integer, nullable=True),
        sa.Column("reset_time", sa.Time, nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "quota_periods",
        sa.Column("quota_period_id", sa.String(64), primary_key=True),
        sa.Column("period_type", sa.String(16), nullable=False),
        sa.Column("period_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reset_policy_id", sa.String(64), sa.ForeignKey("quota_reset_policies.policy_id"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quota_periods_start", "quota_periods", ["period_start_at"])
    op.create_table(
        "quota_balances",
        sa.Column("quota_balance_id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column(
            "quota_period_id", sa.String(64), sa.ForeignKey("quota_periods.quota_period_id"), nullable=False
        ),
        sa.Column("cost_limit_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("consumed_amount", sa.Numeric(20, 6), nullable=False, server_default="0"),
        sa.Column("remaining_amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("quota_status", sa.String(16), nullable=False, server_default="AVAILABLE"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "quota_period_id", name="uq_user_period"),
    )
    op.create_index("ix_quota_balances_user", "quota_balances", ["user_id"])
    op.create_index("ix_quota_balances_period", "quota_balances", ["quota_period_id"])

    op.create_table(
        "usage_logs",
        sa.Column("usage_log_id", sa.String(64), primary_key=True),
        sa.Column("gateway_request_id", sa.String(128), nullable=False, unique=True),
        sa.Column("trace_id", sa.String(128), nullable=True),
        sa.Column("api_key_id", sa.String(64), sa.ForeignKey("api_keys.api_key_id"), nullable=True),
        sa.Column("api_key_mask", sa.String(64), nullable=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("enterprise_openapi_id", sa.String(64), nullable=True),
        sa.Column("provider_id", sa.String(64), nullable=True),
        sa.Column("model_id", sa.String(64), sa.ForeignKey("models.model_id"), nullable=True),
        sa.Column("model_name_snapshot", sa.String(256), nullable=True),
        sa.Column("request_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_status", sa.String(32), nullable=False, server_default="PROVIDER_IN_FLIGHT"),
        sa.Column("prompt_content", sa.JSON, nullable=True),
        sa.Column("response_content", sa.JSON, nullable=True),
        sa.Column("input_tokens", sa.BigInteger, nullable=True),
        sa.Column("output_tokens", sa.BigInteger, nullable=True),
        sa.Column("total_tokens", sa.BigInteger, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usage_logs_trace", "usage_logs", ["trace_id"])
    op.create_index("ix_usage_logs_user", "usage_logs", ["user_id"])
    op.create_index("ix_usage_logs_model", "usage_logs", ["model_id"])
    op.create_index("ix_usage_logs_started", "usage_logs", ["request_started_at"])

    op.create_table(
        "cost_records",
        sa.Column("cost_record_id", sa.String(64), primary_key=True),
        sa.Column("usage_log_id", sa.String(64), sa.ForeignKey("usage_logs.usage_log_id"), nullable=False, unique=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("api_key_id", sa.String(64), sa.ForeignKey("api_keys.api_key_id"), nullable=False),
        sa.Column("model_id", sa.String(64), sa.ForeignKey("models.model_id"), nullable=False),
        sa.Column("quota_period_id", sa.String(64), nullable=True),
        sa.Column("input_tokens", sa.BigInteger, nullable=False),
        sa.Column("output_tokens", sa.BigInteger, nullable=False),
        sa.Column("input_unit_price_per_million", sa.Numeric(20, 6), nullable=False),
        sa.Column("output_unit_price_per_million", sa.Numeric(20, 6), nullable=False),
        sa.Column("input_cost", sa.Numeric(20, 6), nullable=False),
        sa.Column("output_cost", sa.Numeric(20, 6), nullable=False),
        sa.Column("total_cost", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("cost_calculation_status", sa.String(48), nullable=False, server_default="CALCULATED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_cost_records_user", "cost_records", ["user_id"])

    op.create_table(
        "transactional_outbox",
        sa.Column("outbox_id", sa.String(64), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("aggregate_type", sa.String(128), nullable=False),
        sa.Column("aggregate_id", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(128), nullable=True),
    )


def downgrade() -> None:
    for tbl in [
        "transactional_outbox",
        "cost_records",
        "usage_logs",
        "quota_balances",
        "quota_periods",
        "quota_reset_policies",
        "api_key_secret_cache",
        "api_keys",
        "enterprise_openapis",
        "models",
        "llm_providers",
        "platform_sessions",
        "login_challenges",
        "users",
        "role_permissions",
        "permission_actions",
        "roles",
    ]:
        op.drop_table(tbl)
