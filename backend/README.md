# Kobo & Cents backend

FastAPI backend for Kobo & Cents, a Nigerian (NGX) and US stock
research platform. Never a trading platform, no order execution, no
broker integration, at any stage.

Full architecture and reasoning: `docs/backend-architecture/` at the
repo root (`00.md` stack, `01.md` data structures and algorithms,
`02.md` caching and schema gaps, `03-phases.md` the build roadmap this
code is being built from).

## Stack

FastAPI, PostgreSQL (SQLAlchemy Core + Alembic), Celery + Redis,
Mailtrap, Paystack/Flutterwave, Cloudflare Turnstile, Sentry, PostHog,
SlowAPI, Argon2id. Reasoning for each in `docs/backend-architecture/00.md`.

## Local development

```bash
cp .env.example .env   # fill in real values, never commit .env
docker compose up      # Postgres, Redis, the API, and a Celery worker
```

The API serves at `http://localhost:8000`, health check at
`GET /health`.

## Testing and linting

```bash
ruff check .
ruff format .
pytest
```

CI runs both on every push, see `.github/workflows/backend-ci.yml` at
the repo root.
