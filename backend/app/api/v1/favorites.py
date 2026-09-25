import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.market import _resolve_stock
from app.core.deps import get_current_user
from app.core.numeric import floatify
from app.db.session import get_db
from app.models.market_data import stock_prices_current, stock_scores_current, stocks
from app.models.portfolio import favorites
from app.schemas.favorites import (
    AddFavoriteRequest,
    FavoriteItem,
    FavoritesResponse,
    UpdateFavoriteStatusRequest,
)

router = APIRouter(prefix="/favorites", tags=["favorites"])

_VALID_STATUSES = {"watching", "owned"}


def _favorites_select(user_id):
    """One row per (user_id, stock_id), per 01.md, joined out to the
    same display fields the market overview uses. Left joins on
    price/score: a favorited stock that hasn't scored yet (or ever
    failed a refresh) still belongs in the list, per 02.md's own
    graceful-degradation stance, just with those fields null rather
    than the row vanishing."""
    return (
        select(
            favorites.c.stock_id,
            stocks.c.ticker,
            stocks.c.company_name,
            stocks.c.market,
            stocks.c.sector,
            stock_prices_current.c.price,
            stock_prices_current.c.change_percent,
            stock_scores_current.c.composite_score,
            stock_scores_current.c.bucket,
            favorites.c.status,
            favorites.c.created_at,
        )
        .select_from(
            favorites.join(stocks, stocks.c.id == favorites.c.stock_id)
            .join(
                stock_prices_current, stock_prices_current.c.stock_id == stocks.c.id, isouter=True
            )
            .join(
                stock_scores_current, stock_scores_current.c.stock_id == stocks.c.id, isouter=True
            )
        )
        .where(favorites.c.user_id == user_id)
    )


@router.post("", response_model=FavoriteItem, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    body: AddFavoriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> FavoriteItem:
    stock = await _resolve_stock(db, body.ticker, body.market)

    await db.execute(
        pg_insert(favorites)
        .values(user_id=current_user["id"], stock_id=stock["id"], status="watching")
        .on_conflict_do_nothing(index_elements=["user_id", "stock_id"])
    )
    await db.commit()

    result = await db.execute(
        _favorites_select(current_user["id"]).where(favorites.c.stock_id == stock["id"])
    )
    row = result.mappings().first()
    return FavoriteItem(**floatify(dict(row)))


@router.patch("/{stock_id}", response_model=FavoriteItem)
async def update_favorite_status(
    stock_id: uuid.UUID,
    body: UpdateFavoriteStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> FavoriteItem:
    if body.status not in _VALID_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown status: {body.status}")

    result = await db.execute(
        favorites.update()
        .where(favorites.c.user_id == current_user["id"], favorites.c.stock_id == stock_id)
        .values(status=body.status)
        .returning(favorites.c.stock_id)
    )
    if result.first() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not in favorites")
    await db.commit()

    updated = await db.execute(
        _favorites_select(current_user["id"]).where(favorites.c.stock_id == stock_id)
    )
    return FavoriteItem(**floatify(dict(updated.mappings().first())))


@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    stock_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    result = await db.execute(
        favorites.delete()
        .where(favorites.c.user_id == current_user["id"], favorites.c.stock_id == stock_id)
        .returning(favorites.c.stock_id)
    )
    if result.first() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not in favorites")
    await db.commit()


@router.get("", response_model=FavoritesResponse)
async def list_favorites(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> FavoritesResponse:
    """The authenticated user's own list, a direct indexed Postgres
    read, deliberately not cached, per 02.md: already fast, already
    per-user, real invalidation cost for no real benefit."""
    result = await db.execute(
        _favorites_select(current_user["id"]).order_by(favorites.c.created_at.desc())
    )
    items = [FavoriteItem(**floatify(dict(row))) for row in result.mappings().all()]
    return FavoritesResponse(items=items)
