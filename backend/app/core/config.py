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
