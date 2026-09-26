import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.market import _resolve_stock
from app.core.deps import get_current_user
from app.core.rate_limit import READ_LIMIT, WRITE_LIMIT, limiter
from app.db.session import get_db
from app.models.market_data import stocks
from app.models.portfolio import alerts
from app.schemas.alerts import AlertRule, AlertsResponse, CreateAlertRequest
from app.services.entitlements import require_feature

router = APIRouter(prefix="/alerts", tags=["alerts"])

_VALID_RULE_TYPES = {"score_change", "price_threshold"}
_VALID_DIRECTIONS = {"above", "below"}

# Sub-phase 6.1 of docs/backend-architecture/03-phases.md names this
# explicitly: alert rules are gated behind the entitlement check from
# Phase 9, not a locally duplicated paid-tier check, now that Phase 9
# exists. Only creation is gated, not listing or deleting: a user
# whose subscription lapses keeps the ability to see and remove
# alerts they already created, just can't add new ones, the less
# punitive of the two reasonable behaviors here.


def _validate_rule(rule_type: str, rule_config: dict) -> None:
    if rule_type not in _VALID_RULE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown rule_type: {rule_type}")
    if rule_type == "price_threshold":
        direction = rule_config.get("direction")
        price = rule_config.get("price")
        if direction not in _VALID_DIRECTIONS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "rule_config.direction must be 'above' or 'below'"
            )
        if not isinstance(price, int | float) or price <= 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "rule_config.price must be a positive number"
            )


@router.post("", response_model=AlertRule, status_code=status.HTTP_201_CREATED)
@limiter.limit(WRITE_LIMIT)
async def create_alert(
    request: Request,
    body: CreateAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_feature("alerts")),
) -> AlertRule:
    _validate_rule(body.rule_type, body.rule_config)
    stock = await _resolve_stock(db, body.ticker, body.market)

    alert_id = uuid.uuid4()
    await db.execute(
        alerts.insert().values(
            id=alert_id,
            user_id=current_user["id"],
            stock_id=stock["id"],
            rule_type=body.rule_type,
            rule_config=body.rule_config,
            active=True,
        )
    )
    await db.commit()

    result = await db.execute(select(alerts).where(alerts.c.id == alert_id))
    row = result.mappings().first()
    return AlertRule(
        id=row["id"],
        ticker=stock["ticker"],
        company_name=stock["company_name"],
        market=stock["market"],
        rule_type=row["rule_type"],
        rule_config=row["rule_config"],
        active=row["active"],
        created_at=row["created_at"],
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(WRITE_LIMIT)
async def delete_alert(
    request: Request,
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    result = await db.execute(
        alerts.delete()
        .where(alerts.c.id == alert_id, alerts.c.user_id == current_user["id"])
        .returning(alerts.c.id)
    )
    if result.first() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    await db.commit()


@router.get("", response_model=AlertsResponse)
@limiter.limit(READ_LIMIT)
async def list_alerts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AlertsResponse:
    """Not named in Sub-phase 6.1's task list (only POST and DELETE
    are), added for the same reason Favorites got a GET: a resource
    with no way to read it back isn't usable, and this mirrors the
    exact shape app/api/v1/favorites.py already established."""
    result = await db.execute(
        select(
            alerts.c.id,
            alerts.c.rule_type,
            alerts.c.rule_config,
            alerts.c.active,
            alerts.c.created_at,
            stocks.c.ticker,
            stocks.c.company_name,
            stocks.c.market,
        )
        .select_from(alerts.join(stocks, stocks.c.id == alerts.c.stock_id))
        .where(alerts.c.user_id == current_user["id"])
        .order_by(alerts.c.created_at.desc())
    )
    items = [AlertRule(**dict(row)) for row in result.mappings().all()]
    return AlertsResponse(items=items)
