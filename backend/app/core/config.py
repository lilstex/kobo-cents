from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every environment-driven value the backend reads. Real values
    live in .env, never in this file, see .env.example for the full
    list with no real values filled in."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    allowed_origins: str = "http://localhost:3000"

    database_url: str
    redis_url: str

    session_cookie_name: str = "kc_session"
    session_ttl_seconds: int = 1_209_600

    mailtrap_api_token: str = ""
    mailtrap_sandbox_inbox_id: str = ""

    paystack_secret_key: str = ""
    flutterwave_secret_key: str = ""
    # A separate secret from flutterwave_secret_key: Flutterwave's
    # webhook verification is a static hash set in their dashboard,
    # sent back verbatim on every webhook and compared directly, not
    # an HMAC of the payload the way Paystack's is.
    flutterwave_webhook_secret_hash: str = ""

    # No real business decision exists yet on pricing, per
    # docs/01_product.md's monetization section: Stage 2's paywall
    # decisions get made "based on what Stage 1's usage data actually
    # shows," not guessed at here. Placeholder values, explicitly
    # flagged in docs/open-items.md, not a real price.
    subscription_price_ngn: int = 2_500
    subscription_price_usd: int = 5

    turnstile_secret_key: str = ""

    sentry_dsn: str = ""
    posthog_api_key: str = ""
    posthog_host: str = "https://app.posthog.com"

    alpha_vantage_api_key: str = ""
    anthropic_api_key: str = ""

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
