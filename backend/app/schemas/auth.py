from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginChallengeRequest(BaseModel):
    enterprise_email: EmailStr


class LoginChallengeResponse(BaseModel):
    challenge_id: str
    enterprise_email_mask: str
    expires_at: datetime
    # Dev convenience: when EMAIL_MODE=console, expose the password so the UI can show it.
    dev_random_password: Optional[str] = None


class LoginSessionRequest(BaseModel):
    challenge_id: str
    enterprise_email: EmailStr
    random_password: str = Field(min_length=4, max_length=32)


class UserContext(BaseModel):
    user_id: str
    enterprise_email: EmailStr
    role_id: str
    role_name: str
    cost_limit_amount: Decimal
    cost_limit_source: str
    account_status: str
    created_at: datetime
    updated_at: datetime
    version: int


class LoginSessionResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserContext
    permissions: List[str]


class RefreshTokenRequest(BaseModel):
    refresh_token: str
