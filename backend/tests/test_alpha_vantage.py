import httpx
import pytest

from app.integrations.market_data.alpha_vantage import AlphaVantageProvider, _num
from app.integrations.market_data.base import ProviderNotConfiguredError


def test_num_parses_a_real_numeric_string():
    assert _num("123.45") == 123.45


def test_num_treats_the_literal_string_none_as_missing():
    """Alpha Vantage's actual quirk, not a hypothetical: a field it
    doesn't have comes back as the string "None", not JSON null."""
    assert _num("None") is None


def test_num_handles_empty_string_and_real_none():
    assert _num("") is None
    assert _num(None) is None


def test_raises_a_clear_error_without_an_api_key(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.market_data.alpha_vantage.settings.alpha_vantage_api_key", ""
    )
    with pytest.raises(ProviderNotConfiguredError):
        AlphaVantageProvider()


async def test_fetch_maps_a_realistic_response_shape(monkeypatch):
    monkeypatch.setattr(
        "app.integrations.market_data.alpha_vantage.settings.alpha_vantage_api_key", "test-key"
    )

    responses = {
        "OVERVIEW": {"SharesOutstanding": "1000000", "DividendPerShare": "None", "EPS": "6.10"},
        "BALANCE_SHEET": {
            "annualReports": [
                {
                    "totalCurrentAssets": "450000000",
                    "totalCurrentLiabilities": "300000000",
                    "inventory": "150000000",
                    "totalShareholderEquity": "800000000",
                    "shortLongTermDebtTotal": "200000000",
                }
            ]
        },
        "INCOME_STATEMENT": {
            "annualReports": [
                {"netIncome": "196800000", "totalRevenue": "5000000000"},
                {"totalRevenue": "4200000000"},
            ]
        },
        "CASH_FLOW": {
            "annualReports": [
                {"operatingCashflow": "900000000", "capitalExpenditures": "250000000"}
            ]
        },
        "GLOBAL_QUOTE": {"Global Quote": {"05. price": "91.40"}},
    }

    async def fake_get(self, url, params=None, **kwargs):
        request = httpx.Request("GET", url)
        return httpx.Response(200, json=responses[params["function"]], request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    provider = AlphaVantageProvider()
    result = await provider.fetch("EXAMPLE")

    assert result.data_source == "provider"
    assert result.price == 91.40
    assert result.current_assets == 450_000_000
    assert result.dividend_per_share is None  # "None" string correctly became real None
    assert result.previous_year_revenue == 4_200_000_000
    assert result.invested_capital == 800_000_000 + 200_000_000
