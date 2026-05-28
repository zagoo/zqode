from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import Field

from app.schemas.response import BizModel as BaseModel


class APIKeyCreate(BaseModel):
    key_name: str = Field(min_length=1, max_length=128)
    expires_at: datetime


class APIKeyOut(BaseModel):
    api_key_id: str
    owner_user_id: str
    key_name: str
    api_key_mask: str
    application_date: datetime
    expires_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    version: int


class APIKeyCreateResponse(BaseModel):
    api_key: APIKeyOut
    api_key_secret: Optional[str]
    api_key_secret_available: bool
    message: Optional[str] = None


class APIKeyStatusUpdate(BaseModel):
    status: str  # ENABLED | DISABLED


class WorkbenchModelOut(BaseModel):
    model_id: str
    provider_id: str
    provider_name: str
    model_name: str
    input_price_per_million_tokens: Decimal
    output_price_per_million_tokens: Decimal
    currency: str


class WorkbenchOpenAPIOut(BaseModel):
    openapi_id: str
    api_name: str
    api_type: str
    gateway_url: str
    usage_description: Optional[str]
