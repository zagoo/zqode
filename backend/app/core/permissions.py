"""Canonical permission namespace per FDD §1.7."""

PLATFORM_PERMISSIONS = [
    ("platform.provider.create", "M02"),
    ("platform.provider.read", "M02"),
    ("platform.provider.update", "M02"),
    ("platform.provider.delete", "M02"),
    ("platform.model.create", "M02"),
    ("platform.model.read", "M02"),
    ("platform.model.update", "M02"),
    ("platform.model.delete", "M02"),
    ("platform.openapi.create", "M02"),
    ("platform.openapi.read", "M02"),
    ("platform.openapi.update", "M02"),
    ("platform.openapi.delete", "M02"),
    ("platform.user.create", "M02"),
    ("platform.user.read", "M02"),
    ("platform.user.update", "M02"),
    ("platform.user.delete", "M02"),
    ("platform.role.create", "M02"),
    ("platform.role.read", "M02"),
    ("platform.role.update", "M02"),
    ("platform.role.delete", "M02"),
    ("platform.api_key.read_all", "M02"),
    ("platform.api_key.extend_expiry", "M02"),
    ("platform.quota_policy.read", "M02"),
    ("platform.quota_policy.update", "M02"),
]

WORKBENCH_PERMISSIONS = [
    ("workbench.api_key.create", "M03"),
    ("workbench.api_key.read_own", "M03"),
    ("workbench.api_key.update_status_own", "M03"),
    ("workbench.api_key.delete_own", "M03"),
    ("workbench.model.read", "M03"),
    ("workbench.openapi.read", "M03"),
]

ANALYTICS_PERMISSIONS = [
    ("analytics.personal.read", "M05"),
    ("analytics.ranking.read", "M05"),
    ("analytics.prompt_category.read", "M05"),
    ("analytics.detail.read", "M05"),
    ("analytics.summary.read", "M05"),
]

ALL_PERMISSIONS = PLATFORM_PERMISSIONS + WORKBENCH_PERMISSIONS + ANALYTICS_PERMISSIONS


def system_administrator_permissions() -> list[str]:
    return [p for p, _ in ALL_PERMISSIONS]


def team_manager_permissions() -> list[str]:
    return [p for p, _ in WORKBENCH_PERMISSIONS] + [p for p, _ in ANALYTICS_PERMISSIONS]


def normal_user_permissions() -> list[str]:
    return [p for p, _ in WORKBENCH_PERMISSIONS] + [
        "analytics.personal.read",
        "analytics.ranking.read",
        "analytics.prompt_category.read",
    ]
