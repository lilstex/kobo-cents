import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateAlertRequest(BaseModel):
    ticker: str
    market: str
    rule_type: str  # "score_change" | "price_threshold"
    # Empty for score_change (per app/services/alerts.py: it fires on
    # any bucket transition, nothing to configure). For
    # price_threshold: {"direction": "above" | "below", "price": float}.
    rule_config: dict = {}


class AlertRule(BaseModel):
    id: uuid.UUID
    ticker: str
    company_name: str
    market: str
    rule_type: str
    rule_config: dict
    active: bool
    created_at: datetime


class AlertsResponse(BaseModel):
    items: list[AlertRule]
