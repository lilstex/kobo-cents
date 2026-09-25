from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.integrations.market_data.base import FetchedFinancials, ProviderNotConfiguredError

_BASE_URL = "https://www.alphavantage.co/query"


def _num(value: str | None) -> float | None:
    """Alpha Vantage returns every figure as a string, and "None" as
    the literal string "None" for a value it doesn't have, not JSON
    null. Both collapse to a real None here rather than crashing on
    float("None") or silently becoming the string itself."""
    if value is None or value == "None" or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


class AlphaVantageProvider:
    """The US provider behind the MarketDataProvider interface, per
    docs/backend-architecture/00.md and 03-phases.md's Sub-phase 3.1.

    Note: field names below match Alpha Vantage's OVERVIEW,
    BALANCE_SHEET, INCOME_STATEMENT, CASH_FLOW, and GLOBAL_QUOTE
    endpoints as documented at the time this was written, unverified
    against a live key, same honest caveat as the NG research agent,
    a third-party API's exact response shape is worth confirming
    against a real call before this runs in anger.
    """

    def __init__(self) -> None:
        if not settings.alpha_vantage_api_key:
            raise ProviderNotConfiguredError("ALPHA_VANTAGE_API_KEY is not configured")

    async def fetch(self, ticker: str, company_name: str = "") -> FetchedFinancials:
        # company_name unused: Alpha Vantage looks up by ticker symbol
        # alone. Part of the shared MarketDataProvider signature so
        # the refresh job can call either provider identically.
        async with httpx.AsyncClient(timeout=15.0) as client:
            overview, balance_sheet, income_statement, cash_flow, quote = [
                (
                    await client.get(
                        _BASE_URL,
                        params={
                            "function": fn,
                            "symbol": ticker,
                            "apikey": settings.alpha_vantage_api_key,
                        },
                    )
                ).json()
                for fn in (
                    "OVERVIEW",
                    "BALANCE_SHEET",
                    "INCOME_STATEMENT",
                    "CASH_FLOW",
                    "GLOBAL_QUOTE",
                )
            ]

        latest_balance = (balance_sheet.get("annualReports") or [{}])[0]
        latest_income = (income_statement.get("annualReports") or [{}])[0]
        previous_income = (
            (income_statement.get("annualReports") or [{}, {}])[1]
            if len(income_statement.get("annualReports") or []) > 1
            else {}
        )
        latest_cash_flow = (cash_flow.get("annualReports") or [{}])[0]
        quote_data = quote.get("Global Quote", {})

        return FetchedFinancials(
            ticker=ticker,
            statement_date=datetime.now(UTC),
            price=_num(quote_data.get("05. price")),
            current_assets=_num(latest_balance.get("totalCurrentAssets")),
            current_liabilities=_num(latest_balance.get("totalCurrentLiabilities")),
            inventory=_num(latest_balance.get("inventory")),
            shareholders_equity=_num(latest_balance.get("totalShareholderEquity")),
            shares_outstanding=_num(overview.get("SharesOutstanding")),
            net_income=_num(latest_income.get("netIncome")),
            revenue=_num(latest_income.get("totalRevenue")),
            previous_year_revenue=_num(previous_income.get("totalRevenue")),
            operating_profit_after_tax=_num(latest_income.get("netIncome")),
            invested_capital=(
                None
                if _num(latest_balance.get("totalShareholderEquity")) is None
                or _num(latest_balance.get("shortLongTermDebtTotal")) is None
                else _num(latest_balance.get("totalShareholderEquity"))
                + _num(latest_balance.get("shortLongTermDebtTotal"))
            ),
            cash_from_operations=_num(latest_cash_flow.get("operatingCashflow")),
            capex=_num(latest_cash_flow.get("capitalExpenditures")),
            dividend_per_share=_num(overview.get("DividendPerShare")),
            eps=_num(overview.get("EPS")),
            data_source="provider",
        )
