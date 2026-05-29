"""Business error codes mapped to HTTP status."""
from fastapi import HTTPException, status


class BizError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "details": details or {}})


def validation_error(message: str = "Request validation failed.", details: dict | None = None) -> BizError:
    return BizError(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", message, details)


def auth_required() -> BizError:
    return BizError(status.HTTP_401_UNAUTHORIZED, "AUTH_REQUIRED", "Authentication is required.")


def invalid_session() -> BizError:
    return BizError(status.HTTP_401_UNAUTHORIZED, "INVALID_SESSION", "Session is invalid or expired.")


def permission_denied(message: str = "Permission denied.") -> BizError:
    return BizError(status.HTTP_403_FORBIDDEN, "PERMISSION_DENIED", message)


def not_found(message: str = "Resource not found.") -> BizError:
    return BizError(status.HTTP_404_NOT_FOUND, "RESOURCE_NOT_FOUND", message)


def version_conflict() -> BizError:
    return BizError(status.HTTP_412_PRECONDITION_FAILED, "VERSION_CONFLICT", "Resource version mismatch.")


def duplicate_resource(message: str = "Duplicate resource.") -> BizError:
    return BizError(status.HTTP_409_CONFLICT, "DUPLICATE_RESOURCE", message)


def user_disabled() -> BizError:
    return BizError(status.HTTP_403_FORBIDDEN, "USER_DISABLED", "Account is disabled.")


def invalid_login_challenge() -> BizError:
    return BizError(status.HTTP_400_BAD_REQUEST, "INVALID_LOGIN_CHALLENGE", "Login challenge is invalid or expired.")


def invalid_random_password() -> BizError:
    return BizError(status.HTTP_400_BAD_REQUEST, "INVALID_RANDOM_PASSWORD", "The random password is incorrect.")


def api_key_invalid() -> BizError:
    return BizError(status.HTTP_401_UNAUTHORIZED, "API_KEY_INVALID", "API Key is invalid.")


def api_key_disabled() -> BizError:
    return BizError(status.HTTP_403_FORBIDDEN, "API_KEY_DISABLED", "API Key is disabled.")


def api_key_expired() -> BizError:
    return BizError(status.HTTP_403_FORBIDDEN, "API_KEY_EXPIRED", "API Key is expired.")


def api_key_validity_exceeded() -> BizError:
    return BizError(status.HTTP_422_UNPROCESSABLE_ENTITY, "API_KEY_VALIDITY_EXCEEDED", "API Key validity exceeds role limit.")


def api_key_ownership_violation() -> BizError:
    return BizError(status.HTTP_403_FORBIDDEN, "API_KEY_OWNERSHIP_VIOLATION", "You do not own this API Key.")


def quota_exceeded() -> BizError:
    return BizError(status.HTTP_429_TOO_MANY_REQUESTS, "QUOTA_EXCEEDED", "Quota has been exceeded.")


def model_not_found() -> BizError:
    return BizError(status.HTTP_404_NOT_FOUND, "MODEL_NOT_FOUND", "Model is not configured.")


def provider_not_configured() -> BizError:
    return BizError(status.HTTP_502_BAD_GATEWAY, "PROVIDER_NOT_CONFIGURED", "Provider is not configured.")


def provider_request_failed(message: str = "Provider request failed.") -> BizError:
    return BizError(status.HTTP_502_BAD_GATEWAY, "PROVIDER_REQUEST_FAILED", message)


def token_usage_missing() -> BizError:
    return BizError(status.HTTP_502_BAD_GATEWAY, "TOKEN_USAGE_MISSING", "Provider response did not include token usage.")


def email_delivery_failed() -> BizError:
    return BizError(status.HTTP_502_BAD_GATEWAY, "EMAIL_DELIVERY_FAILED", "Could not send the login code. Please try again.")
