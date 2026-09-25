from datetime import UTC, datetime

import anthropic

from app.core.config import settings
from app.integrations.market_data.base import FetchedFinancials, ProviderNotConfiguredError

_MODEL = "claude-sonnet-5"

# One tool call, forced, per docs/backend-architecture/00.md: the
# model researches using web search, then must report through this
# exact schema, never free text left for the caller to parse
# hopefully. Every field nullable, per 01.md's missing-metric
# handling, a figure the research genuinely can't find is None, not a
# guess dressed up as a real number.
_REPORT_TOOL = {
    "name": "report_financials",
    "description": (
        "Report the researched financial figures for one company, with the source URL behind each."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "statement_date": {
                "type": "string",
                "description": "ISO date of the most recent financial statement used",
            },
            "price": {"type": ["number", "null"]},
            "current_assets": {"type": ["number", "null"]},
            "current_liabilities": {"type": ["number", "null"]},
            "inventory": {"type": ["number", "null"]},
            "shareholders_equity": {"type": ["number", "null"]},
            "shares_outstanding": {"type": ["number", "null"]},
            "net_income": {"type": ["number", "null"]},
            "revenue": {"type": ["number", "null"]},
            "previous_year_revenue": {"type": ["number", "null"]},
            "operating_profit_after_tax": {"type": ["number", "null"]},
            "invested_capital": {"type": ["number", "null"]},
            "cash_from_operations": {"type": ["number", "null"]},
            "capex": {"type": ["number", "null"]},
            "dividend_per_share": {"type": ["number", "null"]},
            "eps": {"type": ["number", "null"]},
            "source_urls": {
                "type": "object",
                "description": "Field name to the URL that figure came from",
                "additionalProperties": {"type": "string"},
            },
        },
        "required": ["statement_date", "source_urls"],
    },
}


class NGResearchAgent:
    """The LLM research mechanism from docs/backend-architecture/00.md,
    the resolved answer to "no mature NGX data API exists." Also used
    to fill any single metric gap a US provider doesn't supply
    directly, per Sub-phase 3.1, same schema, same citation
    requirement, not a second, separately-built path.

    Note: written against the Anthropic Messages API's tool-use and
    web-search-tool shape as documented at the time this was written.
    Verify the web-search tool's exact type string against Anthropic's
    current API reference before this runs against a real key for the
    first time, API surfaces move; nothing in this codebase has
    exercised this against a live key yet, unlike everything else in
    this project, which was verified against real infrastructure.
    """

    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise ProviderNotConfiguredError("ANTHROPIC_API_KEY is not configured")
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def fetch(self, ticker: str, company_name: str) -> FetchedFinancials:
        response = await self._client.messages.create(
            model=_MODEL,
            max_tokens=2048,
            tools=[{"type": "web_search_20250305", "name": "web_search"}, _REPORT_TOOL],
            tool_choice={"type": "tool", "name": "report_financials"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Research {company_name} ({ticker}), listed on the Nigerian "
                        "Stock Exchange (NGX). Find its most recent price and the "
                        "financial figures needed for liquidity, profitability, "
                        "valuation, and dividend analysis. Use real, current sources, "
                        "NGX's own site, the company's investor relations page, or "
                        "reputable Nigerian financial press. Leave a figure null if "
                        "you cannot find it from a real source, never estimate. "
                        "Report every figure through report_financials, with the "
                        "source URL for each."
                    ),
                }
            ],
        )

        tool_use = next(block for block in response.content if block.type == "tool_use")
        data = tool_use.input

        return FetchedFinancials(
            ticker=ticker,
            statement_date=datetime.fromisoformat(data["statement_date"]).replace(tzinfo=UTC),
            price=data.get("price"),
            current_assets=data.get("current_assets"),
            current_liabilities=data.get("current_liabilities"),
            inventory=data.get("inventory"),
            shareholders_equity=data.get("shareholders_equity"),
            shares_outstanding=data.get("shares_outstanding"),
            net_income=data.get("net_income"),
            revenue=data.get("revenue"),
            previous_year_revenue=data.get("previous_year_revenue"),
            operating_profit_after_tax=data.get("operating_profit_after_tax"),
            invested_capital=data.get("invested_capital"),
            cash_from_operations=data.get("cash_from_operations"),
            capex=data.get("capex"),
            dividend_per_share=data.get("dividend_per_share"),
            eps=data.get("eps"),
            data_source="ng_research_agent",
            source_urls=data.get("source_urls") or {},
        )
