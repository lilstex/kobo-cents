# Kobo & Cents

A stock research platform for the Nigerian (NGX) and US markets. It brings
price data, company fundamentals, and a sector-relative scoring engine
together in one place, so you can understand a stock before you decide
anything about it.

Kobo & Cents is never a trading platform. There is no order execution, no
broker integration, and no plan to add either. It is a research and
tracking tool, built and operated by ShotNub Solutions LTD.

## What it does

- Tracks NGX and US listed stocks: current price, price history, and raw
  company fundamentals.
- Scores every stock against its own sector peers using percentile ranking
  across five metric categories (valuation, profitability, growth,
  financial health, and dividends), then explains the score in plain
  sentences instead of a bare number.
- Refreshes data on a schedule, separately for each market, using Alpha
  Vantage for US data and an LLM-backed research agent for NGX data,
  where no mature market data API exists.
- Accounts are email and password based, with email verification required
  before login, password reset, and password change while signed in.
- Public landing page and glossary need no account. The scored,
  authenticated research screens sit behind login.

## How it is built

**Backend**: FastAPI, PostgreSQL (SQLAlchemy Core, not the ORM, plus
Alembic for migrations), Celery and Redis for background jobs, scheduled
refresh, caching, rate limiting, and sessions. Argon2id for passwords.
Mailtrap for transactional email. Cloudflare Turnstile for bot
mitigation. Sentry and PostHog for observability. Anthropic's API powers
the NGX research agent.

**Frontend**: Next.js (App Router, TypeScript), Tailwind CSS, an
OpenAPI-generated typed API client, React Hook Form with Zod, and MDX for
the glossary and legal pages.

Full reasoning for every technical decision lives in `docs/`, which is
not tracked in this repository except for `docs/deployment-vps.md`.

## Project structure

```
kobo&cents/
  backend/     FastAPI application, Celery workers, Alembic migrations
  frontend/    Next.js application
  docs/        Architecture and planning docs (mostly untracked, local only)
```

Inside `backend/app/`: `api/` (route handlers), `core/` (config, security,
sessions, rate limiting), `db/` (database session setup), `integrations/`
(email, market data providers, payments), `models/` (SQLAlchemy table
definitions), `schemas/` (Pydantic request and response models),
`services/` (scoring and explainability logic), `workers/` (Celery app and
tasks).

Inside `frontend/`: `app/` (routes, grouped into `(marketing)` and
`(auth)`), `components/`, `content/` (MDX glossary and legal pages),
`lib/` (API client, glossary and legal helpers), `image-assets/` (logos,
favicons, and PWA icons).

## Prerequisites

- Python 3.12 or newer
- Node.js 24 or newer
- Docker and Docker Compose, if you want to run the backend's services
  that way
- PostgreSQL 17 and Redis 7, if you want to run them natively instead of
  through Docker

## Running locally

The backend and frontend are set up independently. The frontend has no
Docker image yet, so it always runs with Node directly, whichever way you
choose to run the backend.

### Backend, with Docker

This starts Postgres, Redis, the API, and a Celery worker together.

```bash
cd backend
cp .env.example .env   # fill in real values, never commit .env
docker compose up
```

The API serves at `http://localhost:8000`, health check at `GET /health`.
Postgres is reachable on the host at `localhost:5433` and Redis at
`localhost:6380` (not the usual 5432 and 6379, so this does not collide
with a native Postgres or Redis already running on your machine). Inside
the Docker network itself, the API and worker containers reach Postgres
and Redis at their normal internal ports.

Database migrations still need to be applied once the containers are up:

```bash
docker compose exec api alembic upgrade head
```

### Backend, without Docker

Requires a Postgres 17 instance and a Redis 7 instance already running
and reachable.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# edit .env: DATABASE_URL and REDIS_URL should point at your own
# Postgres and Redis instances

alembic upgrade head
uvicorn app.main:app --reload
```

The API serves at `http://localhost:8000`.

To process background jobs (sending email, refreshing market data), run a
Celery worker in a separate terminal, with the same virtual environment
active:

```bash
celery -A app.workers.celery worker --loglevel=info
```

Without a running worker, requests that queue a background job (signup,
password reset, a market data refresh) will accept the request but the
job itself never runs.

### Frontend

There is no Docker path for the frontend yet. It always runs directly
with Node.

```bash
cd frontend
cp .env.example .env.local   # fill in real values, never commit .env.local
npm install
npm run dev
```

Serves at `http://localhost:3000`. Set `NEXT_PUBLIC_API_BASE_URL` in
`.env.local` to wherever the backend is actually running, `http://localhost:8000`
for either backend setup above.

## Environment variables

Both `backend/.env.example` and `frontend/.env.example` are the
authoritative, commented list of every variable each app reads, along
with why each one exists. Copy them, do not guess values, and never
commit the real `.env` or `.env.local` files.

Some integrations (Mailtrap, Turnstile, Sentry, PostHog, Paystack,
Flutterwave) are safe to leave blank in local development. The app falls
back to logging instead of calling the real service, so you can still see
what would have been sent, for example a verification email's contents,
in the backend's log output.

## Testing and linting

Backend, from `backend/` with its virtual environment active:

```bash
ruff check .
ruff format .
pytest
```

Frontend, from `frontend/`:

```bash
npm run lint:oxlint
npm run test      # Vitest, unit and component tests
npm run test:e2e  # Playwright, requires the backend and frontend both running
npm run build     # production build, also runs the TypeScript check
```

CI runs the backend's checks and the frontend's checks independently, see
`.github/workflows/backend-ci.yml` and `.github/workflows/frontend-ci.yml`.

## Regenerating the typed API client

Whenever a backend endpoint changes shape, regenerate the frontend's API
types from the backend's live OpenAPI schema, with the backend running:

```bash
cd frontend
npm run generate:types
```

This writes `frontend/lib/api/schema.d.ts` and should not be hand-edited.

## Company

Kobo & Cents is built and operated by ShotNub Solutions LTD, a
registered Nigerian company.
