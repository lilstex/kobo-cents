from datetime import datetime

from pydantic import BaseModel


class ShareSnapshotItem(BaseModel):
    ticker: str
    company_name: str
    market: str
    sector: str
    status: str
    price: float | None
    change_percent: float | None
    composite_score: float | None
    bucket: str | None


class CreateShareResponse(BaseModel):
    token: str
    share_url: str
    expires_at: datetime


class ShareView(BaseModel):
    items: list[ShareSnapshotItem]
    created_at: datetime
