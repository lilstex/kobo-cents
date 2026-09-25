from app.core.read_cache import bump_data_version, get_data_version


async def test_version_starts_at_zero_for_an_unseen_market():
    assert await get_data_version("TEST_MARKET_A") == 0


async def test_bump_increments_and_persists():
    await bump_data_version("TEST_MARKET_B")
    await bump_data_version("TEST_MARKET_B")
    assert await get_data_version("TEST_MARKET_B") == 2


async def test_markets_are_independent():
    await bump_data_version("TEST_MARKET_C")
    assert await get_data_version("TEST_MARKET_D") == 0
