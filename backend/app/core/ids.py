from ulid import ULID


def new_id(prefix: str) -> str:
    return f"{prefix}_{str(ULID())}"


def user_id() -> str:
    return new_id("usr")


def role_id() -> str:
    return new_id("rol")


def provider_id() -> str:
    return new_id("prv")


def model_id() -> str:
    return new_id("mdl")


def openapi_id() -> str:
    return new_id("eoa")


def api_key_id() -> str:
    return new_id("key")


def challenge_id() -> str:
    return new_id("lch")


def session_id() -> str:
    return new_id("ses")


def quota_policy_id() -> str:
    return new_id("qrp")


def quota_period_id() -> str:
    return new_id("qtp")


def quota_balance_id() -> str:
    return new_id("qbl")


def usage_log_id() -> str:
    return new_id("ulg")


def cost_record_id() -> str:
    return new_id("crd")


def outbox_id() -> str:
    return new_id("evt")


def request_id() -> str:
    return new_id("req")
