import uuid
from datetime import datetime

from pydantic import BaseModel


class AddFavoriteRequest(BaseModel):
    ticker: str
    market: str


class UpdateFavoriteStatusRequest(BaseModel):
    status: str  # "watching" | "owned"


class FavoriteItem(BaseModel):
    # stock_id is exposed here specifically so PATCH/DELETE
    # /favorites/{stock_id} (the path shape docs/backend-architecture/
    # 03-phases.md names literally) has something to target: nothing
    # else in the public API surface hands out this internal id.
    stock_id: uuid.UUID
    ticker: str
    company_name: str
    market: str
    sector: str
    status: str
    price: float | None
    change_percent: float | None
    composite_score: float | None
    bucket: str | None
    created_at: datetime


class FavoritesResponse(BaseModel):
    items: list[FavoriteItem]
