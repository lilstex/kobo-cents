import logging
import re
import time
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.read_cache import get_cached_json, get_data_version
from app.models.market_data import stocks
from app.workers.tasks.refresh_market_data import refresh_market
from tests.test_refresh_market_data import _FAKE_FINANCIALS, FakeProvider, _seed_active_weights

# Reuses the same three real NG Financial Services names and fake
# provider from test_refresh_market_data.py rather than hand-building
# stock_scores_current rows: running the real refresh pipeline gives
# these tests genuine, internally-consistent scored data (percentiles
# that actually match the underlying fundamentals) instead of
# possibly-inconsistent fixtures, and exercises the seam between the
# refresh job and these read endpoints for free.


@pytest.fixture(autouse=True)
def capture_sent_emails(monkeypatch):
    sent = []

    def fake_delay(to, subject, html):
        sent.append({"to": to, "subject": subject, "html": html})

    monkeypatch.setattr("app.api.v1.auth.send_email_task.delay", fake_delay)
    return sent


def _extract_token(html: str) -> str:
    match = re.search(r"token=([^\"&]+)", html)
    assert match, f"no token found in: {html}"
    return match.group(1)


async def _signup_verify_login(client, capture_sent_emails, email: str) -> None:
    """Leaves the client's own cookie jar holding a real session
    afterward, since httpx.AsyncClient persists cookies across
    requests made with the same client instance."""
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "a-real-password", "terms_version": "v1"},
    )
    token = _extract_token(capture_sent_emails[-1]["html"])
    await client.post("/api/v1/auth/verify", json={"token": token})
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "a-real-password"}
    )
    assert response.json()["status"] == "ok"


async def _seed_ng_stocks(db_session) -> None:
    await _seed_active_weights(db_session)
    provider = FakeProvider(_FAKE_FINANCIALS)
    await refresh_market("NG", provider, db_session, cycle_id=uuid.uuid4().hex)


async def test_overview_requires_authentication(client, db_session):
    await _seed_ng_stocks(db_session)
    response = await client.get("/api/v1/markets/NG/overview")
    assert response.status_code == 401


async def test_overview_returns_scored_stocks_ordered_by_score_desc(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "overview-user@example.com")

    response = await client.get("/api/v1/markets/NG/overview")
    assert response.status_code == 200
    body = response.json()

    tickers = [item["ticker"] for item in body["items"]]
    assert set(tickers) == {"GTCO", "ZENITHBANK", "ACCESSCORP"}
    assert body["total"] == 3
    scores = [item["composite_score"] for item in body["items"]]
    assert scores == sorted(scores, reverse=True)
    # GTCO's fundamentals are strictly the strongest of the three fake
    # peers across every metric, so it should rank first.
    assert tickers[0] == "GTCO"


async def test_overview_filters_by_bucket_and_sector(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "filter-user@example.com")

    well = await client.get("/api/v1/markets/NG/overview", params={"bucket": "well"})
    assert well.status_code == 200
    assert [item["ticker"] for item in well.json()["items"]] == ["GTCO"]

    matching_sector = await client.get(
        "/api/v1/markets/NG/overview", params={"sector": "Financial Services"}
    )
    assert matching_sector.json()["total"] == 3

    other_sector = await client.get("/api/v1/markets/NG/overview", params={"sector": "Oil and Gas"})
    assert other_sector.json()["total"] == 0


async def test_overview_respects_pagination(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "page-user@example.com")

    page = await client.get("/api/v1/markets/NG/overview", params={"limit": 1, "offset": 1})
    body = page.json()
    assert body["total"] == 3
    assert len(body["items"]) == 1
    assert body["limit"] == 1
    assert body["offset"] == 1


async def test_overview_populates_the_read_cache(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "cache-user@example.com")

    await client.get("/api/v1/markets/NG/overview")
    version = await get_data_version("NG")
    cached = await get_cached_json(f"overview:NG:all:all:25:0:v{version}")
    assert cached is not None
    assert cached["total"] == 3


async def test_overview_rejects_an_unknown_market(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "market-user@example.com")
    response = await client.get("/api/v1/markets/XX/overview")
    assert response.status_code == 404


async def test_stock_detail_returns_categories_glossary_and_explanation(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "detail-user@example.com")

    response = await client.get("/api/v1/stocks/GTCO")
    assert response.status_code == 200
    body = response.json()

    assert body["ticker"] == "GTCO"
    assert body["bucket"] == "well"
    assert {c["category"] for c in body["categories"]} == {
        "liquidity",
        "equity",
        "profitability",
        "valuation_and_growth",
        "dividends",
    }
    roe_category = next(c for c in body["categories"] if c["category"] == "profitability")
    roe_metric = next(m for m in roe_category["metrics"] if m["key"] == "roe")
    assert roe_metric["value"] == pytest.approx(196.8e6 / 800e6)
    assert roe_metric["percentile"] is not None
    assert len(body["glossary"]) == 11
    assert body["explanation"]
    assert body["scores_as_of"] is not None
    assert body["price_as_of"] is not None


async def test_stock_detail_404_for_unknown_ticker(client, db_session, capture_sent_emails):
    await _signup_verify_login(client, capture_sent_emails, "missing-user@example.com")
    response = await client.get("/api/v1/stocks/NOPE")
    assert response.status_code == 404


async def test_search_finds_by_ticker_and_fuzzy_company_name(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "search-user@example.com")

    by_typo_ticker = await client.get("/api/v1/search", params={"q": "zenit"})
    assert "ZENITHBANK" in [item["ticker"] for item in by_typo_ticker.json()["items"]]

    by_company_name = await client.get("/api/v1/search", params={"q": "guaranty trust"})
    assert "GTCO" in [item["ticker"] for item in by_company_name.json()["items"]]


async def test_compare_requires_two_or_three_tickers(client, db_session, capture_sent_emails):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "compare-user@example.com")

    response = await client.get("/api/v1/compare", params={"tickers": "GTCO"})
    assert response.status_code == 400


async def test_compare_highlights_the_best_stock_per_metric(
    client, db_session, capture_sent_emails
):
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "compare-best-user@example.com")

    response = await client.get("/api/v1/compare", params={"tickers": "GTCO,ZENITHBANK,ACCESSCORP"})
    assert response.status_code == 200
    body = response.json()
    assert {s["ticker"] for s in body["stocks"]} == {"GTCO", "ZENITHBANK", "ACCESSCORP"}
    # GTCO's ROE (196.8e6 / 800e6) beats both other fake peers outright.
    assert body["best_in_comparison"]["roe"] == "GTCO"


async def test_stock_detail_requires_market_to_disambiguate_a_ticker_collision(
    client, db_session, capture_sent_emails
):
    """The schema explicitly allows this (unique on (ticker, market),
    not on ticker alone, per app/models/market_data.py), a real path
    _resolve_stock has to handle, never exercised until now."""
    await _signup_verify_login(client, capture_sent_emails, "collision-user@example.com")
    await db_session.execute(
        stocks.insert().values(
            id=uuid.uuid4(),
            ticker="DUPTICK",
            company_name="NG Namesake Plc",
            market="NG",
            sector="Services",
            listing_status="active",
        )
    )
    await db_session.execute(
        stocks.insert().values(
            id=uuid.uuid4(),
            ticker="DUPTICK",
            company_name="US Namesake Inc",
            market="US",
            sector="Information Technology",
            listing_status="active",
        )
    )

    ambiguous = await client.get("/api/v1/stocks/DUPTICK")
    assert ambiguous.status_code == 400

    resolved = await client.get("/api/v1/stocks/DUPTICK", params={"market": "US"})
    assert resolved.status_code == 200
    assert resolved.json()["company_name"] == "US Namesake Inc"


async def test_overview_cache_skips_the_count_and_rows_queries_once_warm(
    client, db_session, capture_sent_emails, monkeypatch
):
    """The basic load sanity check Phase 11 of docs/backend-
    architecture/03-phases.md asks for on the hottest read path, cache
    both warm and cold: not wall-clock timing (flaky on a shared CI
    runner), the actual, deterministic thing that matters, counted
    directly rather than inferred from how fast a response came back.

    get_current_user (app/core/deps.py) checks the session against
    Redis but still re-reads the user row from Postgres on every
    request to catch a deleted account, so "warm" doesn't mean zero
    Postgres queries, it means the cache skips the overview's own
    count-and-rows queries. That fixed one-query-per-request floor
    from auth is real, expected behaviour, not a caching bug."""
    await _seed_ng_stocks(db_session)
    await _signup_verify_login(client, capture_sent_emails, "load-check-user@example.com")

    call_count = {"n": 0}
    original_execute = AsyncSession.execute

    async def counting_execute(self, *args, **kwargs):
        call_count["n"] += 1
        return await original_execute(self, *args, **kwargs)

    monkeypatch.setattr(AsyncSession, "execute", counting_execute)

    # Cold: the first request for this exact query is a guaranteed
    # cache miss, per the versioned-key scheme in 02.md, and should
    # cost exactly the auth-check query plus the count query plus the
    # rows query, no more.
    call_count["n"] = 0
    cold_start = time.perf_counter()
    cold_response = await client.get("/api/v1/markets/NG/overview")
    cold_elapsed = time.perf_counter() - cold_start
    assert cold_response.status_code == 200
    assert call_count["n"] == 3

    # Warm: 50 repeats of the identical query, simulating real
    # sustained traffic against the hottest read path. Each one still
    # pays the fixed auth-check query, but none of them should re-run
    # the count or rows queries the cold request paid for.
    call_count["n"] = 0
    warm_start = time.perf_counter()
    for _ in range(50):
        warm_response = await client.get("/api/v1/markets/NG/overview")
        assert warm_response.status_code == 200
        assert warm_response.json() == cold_response.json()
    warm_elapsed = time.perf_counter() - warm_start

    assert call_count["n"] == 50
    # Soft, informational timing check, not the load-bearing
    # assertion above: 50 cache hits totalling less than one cold
    # miss would be a surprising regression worth noticing, but this
    # is not asserted strictly to avoid CI flakiness from shared
    # runner noise.
    if warm_elapsed >= cold_elapsed:
        logging.getLogger("app.test").warning(
            "50 warm overview requests (%.4fs) were not faster than 1 cold one (%.4fs)",
            warm_elapsed,
            cold_elapsed,
        )
