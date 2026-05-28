from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from app.schemas.response import BizModel as BaseModel


class TrendPoint(BaseModel):
    period: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost: Decimal


class ModelBreakdown(BaseModel):
    model_id: str
    model_name: str
    total_tokens: int
    total_cost: Decimal


class PersonalConsumption(BaseModel):
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: Decimal
    currency: str
    current_period_consumed: Decimal
    current_period_limit: Decimal
    quota_usage_ratio: float
    trend: List[TrendPoint]
    by_model: List[ModelBreakdown]


class RankingEntry(BaseModel):
    rank: int
    display_name: str
    total_tokens: int
    total_cost: Decimal
    is_current_user: bool


class RankingResponse(BaseModel):
    entries: List[RankingEntry]
    total_users: int


class PromptCategoryStat(BaseModel):
    category_name: str
    total_tokens: int
    total_cost: Decimal
    request_count: int


class ConsumptionDetailRow(BaseModel):
    usage_log_id: str
    time: datetime
    user_email: str
    api_key_mask: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cost: Decimal
    currency: str
    status: str


class SummaryRow(BaseModel):
    period: str
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: Decimal
    currency: str
    request_count: int
