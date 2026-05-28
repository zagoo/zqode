from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional

from pydantic import EmailStr, Field

from app.schemas.response import BizModel as BaseModel


# ---------- Provider ----------
class ProviderCreate(BaseModel):
    provider_name: str = Field(min_length=1, max_length=128)
    api_base_url: str = Field(max_length=2048)
    api_key: str = Field(min_length=1, max_length=2048)
    api_description: Optional[str] = None


class ProviderUpdate(BaseModel):
    provider_name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_description: Optional[str] = None


class ProviderOut(BaseModel):
    provider_id: str
    provider_name: str
    api_base_url: str
    api_key_mask: str
    api_description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


# ---------- Model ----------
class ModelCreate(BaseModel):
    provider_id: str
    model_name: str = Field(min_length=1, max_length=256)
    input_price_per_million_tokens: Decimal = Field(ge=0)
    output_price_per_million_tokens: Decimal = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class ModelUpdate(BaseModel):
    model_name: Optional[str] = None
    input_price_per_million_tokens: Optional[Decimal] = None
    output_price_per_million_tokens: Optional[Decimal] = None
    currency: Optional[str] = None


class ModelOut(BaseModel):
    model_id: str
    provider_id: str
    provider_name: str
    model_name: str
    input_price_per_million_tokens: Decimal
    output_price_per_million_tokens: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


# ---------- OpenAPI ----------
class OpenAPICreate(BaseModel):
    api_name: str = Field(min_length=1, max_length=128)
    api_type: str  # OPENAI_COMPATIBLE | ANTHROPIC_COMPATIBLE
    gateway_url: str
    usage_description: Optional[str] = None


class OpenAPIUpdate(BaseModel):
    api_name: Optional[str] = None
    api_type: Optional[str] = None
    gateway_url: Optional[str] = None
    usage_description: Optional[str] = None


class OpenAPIOut(BaseModel):
    openapi_id: str
    api_name: str
    api_type: str
    gateway_url: str
    usage_description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


# ---------- User ----------
class UserCreate(BaseModel):
    enterprise_email: EmailStr
    role_id: str
    cost_limit_source: str = "ROLE_DEFAULT"
    custom_cost_limit_amount: Optional[Decimal] = None
    account_status: str = "ENABLED"


class UserUpdate(BaseModel):
    role_id: Optional[str] = None
    cost_limit_source: Optional[str] = None
    custom_cost_limit_amount: Optional[Decimal] = None
    account_status: Optional[str] = None


class UserOut(BaseModel):
    user_id: str
    enterprise_email: str
    role_id: str
    role_name: str
    cost_limit_source: str
    cost_limit_amount: Decimal
    account_status: str
    created_at: datetime
    updated_at: datetime
    version: int


# ---------- Role ----------
class RoleCreate(BaseModel):
    role_name: str
    permissions: List[str]
    default_cost_limit_amount: Decimal = Field(ge=0)
    api_key_validity_days: int = Field(gt=0)


class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    permissions: Optional[List[str]] = None
    default_cost_limit_amount: Optional[Decimal] = None
    api_key_validity_days: Optional[int] = None


class RoleOut(BaseModel):
    role_id: str
    role_name: str
    permissions: List[str]
    default_cost_limit_amount: Decimal
    api_key_validity_days: int
    created_at: datetime
    updated_at: datetime
    version: int


# ---------- API Key (admin) ----------
class AdminAPIKeyOut(BaseModel):
    api_key_id: str
    owner_user_id: str
    owner_enterprise_email: str
    key_name: str
    api_key_mask: str
    application_date: datetime
    expires_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


class AdminAPIKeyExtend(BaseModel):
    new_expires_at: datetime
    reason: str = Field(min_length=1, max_length=512)


# ---------- Quota Policy ----------
class QuotaPolicyOut(BaseModel):
    policy_id: str
    reset_mode: str
    reset_day_of_month: Optional[int]
    reset_time: Optional[time]
    timezone: Optional[str]
    created_at: datetime
    updated_at: datetime
    version: int


class QuotaPolicyUpdate(BaseModel):
    reset_mode: str
    reset_day_of_month: Optional[int] = None
    reset_time: Optional[time] = None
    timezone: Optional[str] = "UTC"
