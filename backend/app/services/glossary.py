from dataclasses import dataclass

# Sub-phase 4.2's "static glossary payload": a plain-language
# definition per metric, attached to the stock detail response so
# nobody has to leave the page to look up a term, per 01_product.md.
# No per-request computation, this is fixed data, one entry per
# metric key from app/services/scoring.py. Term and short_definition
# text is kept identical to the matching frontmatter in
# frontend/content/glossary/*.mdx, the frontend's own source of truth
# for the full glossary article, so a term reads the same whether
# someone hits it through this API or the public glossary page.
# `slug` is that same file's slug, for deep-linking to the full entry.


@dataclass(frozen=True)
class GlossaryEntry:
    term: str
    short_definition: str
    slug: str


METRIC_GLOSSARY: dict[str, GlossaryEntry] = {
    "current_ratio": GlossaryEntry(
        term="Current Ratio",
        short_definition=(
            "Whether a company can cover what it owes in the next year with what it can turn "
            "into cash in the next year. Above 1 generally means yes."
        ),
        slug="current-ratio",
    ),
    "quick_ratio": GlossaryEntry(
        term="Quick Ratio",
        short_definition=(
            "Like the current ratio, but stricter, it leaves out inventory, since inventory "
            "doesn't always turn into cash quickly."
        ),
        slug="quick-ratio",
    ),
    "shareholders_equity": GlossaryEntry(
        term="Shareholders' Equity",
        short_definition=(
            "What would be left for shareholders if a company sold everything it owns and paid "
            "off everything it owes."
        ),
        slug="shareholders-equity",
    ),
    "book_value": GlossaryEntry(
        term="Book Value",
        short_definition=(
            "Shareholders' equity, expressed per individual share, what one share is worth on "
            "the company's own books."
        ),
        slug="book-value",
    ),
    "net_profit_margin": GlossaryEntry(
        term="Net Profit Margin",
        short_definition=(
            "How much of every naira or dollar in revenue actually turns into profit after "
            "every cost is paid."
        ),
        slug="net-profit-margin",
    ),
    "roe": GlossaryEntry(
        term="Return on Equity (ROE)",
        short_definition=(
            "How much profit the company generates for every naira or dollar shareholders have "
            "invested. Higher generally means the company uses its money more efficiently."
        ),
        slug="return-on-equity",
    ),
    "roic": GlossaryEntry(
        term="Return on Invested Capital (ROIC)",
        short_definition=(
            "How efficiently a company turns the total capital invested in it, debt and equity "
            "both, into profit."
        ),
        slug="return-on-invested-capital",
    ),
    "pe_ratio": GlossaryEntry(
        term="Price-to-Earnings (P/E) Ratio",
        short_definition=(
            "How much investors are currently paying for one naira or dollar of the company's "
            "annual earnings. Higher usually means more growth is already priced in."
        ),
        slug="price-to-earnings-ratio",
    ),
    "free_cash_flow": GlossaryEntry(
        term="Free Cash Flow (FCF)",
        short_definition=(
            "The actual cash a company has left after running the business and investing in "
            "it, the cash it could return to shareholders, pay down debt with, or reinvest."
        ),
        slug="free-cash-flow",
    ),
    "revenue_growth_rate": GlossaryEntry(
        term="Revenue Growth Rate",
        short_definition=(
            "How much a company's revenue has grown compared to the same period a year earlier."
        ),
        slug="revenue-growth-rate",
    ),
    "dividend_yield": GlossaryEntry(
        term="Dividend Yield",
        short_definition=(
            "How much a company pays out in dividends each year, as a percentage of the "
            "current share price."
        ),
        slug="dividend-yield",
    ),
}
