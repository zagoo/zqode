# ZQode — Internal Enterprise LLM API Gateway Platform

An OpenAI/Anthropic-compatible gateway in front of external LLM providers, with
per-user API keys, quota tracking, and usage analytics. Built to the
[FDD](./FDD.md) — 6 modules (M00–M05), 7 background services (BS01–BS07),
FastAPI + Vue 3.

## Quick start (Docker)

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend  | http://localhost:8000 (Swagger at `/docs`) |
| OpenAPI  | http://localhost:8000/openapi.json |
| Postgres | localhost:5432 (user `zqode` / pass `zqode_dev`) |

On first boot the bootstrap routine seeds the canonical permission namespace,
the three built-in roles (System Administrator, Team Manager, Normal User),
and the initial admin user from `INITIAL_ADMIN_ENTERPRISE_EMAIL`
(default `admin@example.com`).

`EMAIL_MODE=console` (default) prints the random login code to the backend
container logs so you can sign in without an SMTP server. Set `EMAIL_MODE=smtp`
with the `SMTP_*` settings to email the code to users in production.

## Production deployment (online formal mode)

`docker-compose.yml` is **developer mode** (Vite dev server, `uvicorn --reload`,
bind-mounted source, hardcoded dev secrets). For a single-host production
("online formal") deployment use `docker-compose.prod.yml`:

```bash
cp .env.example .env.prod          # then fill in the CHANGE_ME secrets
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

The frontend is then served at `http://<host>:${HTTP_PORT:-80}`.

How it differs from dev mode:

| | Dev (`docker-compose.yml`) | Prod (`docker-compose.prod.yml`) |
|---|---|---|
| Frontend | Vite dev server `:5173`, source mounted, HMR | `npm run build` → static assets served by **nginx**, which reverse-proxies `/api` → backend |
| Backend | `uvicorn --reload`, 1 worker, source mounted | `uvicorn --workers ${UVICORN_WORKERS}`, no reload, code baked into the image, runs as non-root |
| Migrations / seed | run inline on every start | a one-shot `migrate` service runs `alembic upgrade head` then seeds **once**, before workers start |
| Secrets | hardcoded in the compose file | required via `.env.prod`; a missing `JWT_SECRET_KEY` / `POSTGRES_PASSWORD` aborts startup |
| Exposure | Postgres + backend published to host | only nginx (`:80`) is published; Postgres + backend stay on the internal network |

The SPA calls the API with relative paths, so nginx serving the SPA and
proxying `/api` keeps everything same-origin (no CORS). Because the backend is
no longer published to the host, FastAPI's `/docs` and `/openapi.json` are
reachable only from inside the compose network — regenerate the typed client
(`npm run openapi:gen`) against the **dev** stack.

### Before going live — known gaps

- **Login codes are emailed when `EMAIL_MODE=smtp`** (configure the `SMTP_*`
  settings). In the default `console` mode the code is written to the backend
  logs instead of being emailed.
- **Provider API keys are not encrypted at rest** (`api_key_ciphertext` stores
  plaintext today — see "Known scope-limits"). Add a KMS/libsodium box first.
- **TLS is not included.** Terminate HTTPS at an upstream load balancer, or add
  a TLS-terminating reverse proxy (e.g. Caddy/Traefik) in front of nginx and
  map `:443`.

## End-to-end smoke test (no Postgres needed)

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt aiosqlite
.venv/bin/python tests/smoke_test.py
```

Exercises auth, admin CRUD, workbench API-key creation, a mock-provider
gateway call, analytics, and a couple of negative paths. ~30 HTTP requests,
runs in under a second against in-memory SQLite.

The login-code email sender has a focused unit test that needs no dependencies
(stdlib only — it stubs config/errors and a fake SMTP server):

```bash
cd backend && python3 tests/test_email.py
```

## Architecture

### Backend (`backend/`)
- **FastAPI** with async/await end-to-end
- **SQLAlchemy 2.0** (`Mapped[...]` / `mapped_column`) + **Alembic** migrations
- **Pydantic v2** for request/response schemas wrapped in
  `ApiResponse[T]` / `PageData[T]`
- **PyJWT** dual-token auth — short-lived access, long-lived refresh
- API Key secrets are deterministically sha256-hashed for O(1) gateway lookup
  and never stored in plaintext

### Frontend (`frontend/`)
- **Vue 3** + Composition API + `<script setup lang="ts">` + **TypeScript**
- **Vite** with `/api` reverse-proxy to the backend
- **Pinia** setup-style stores (`store/auth.ts`, `store/shell.ts`)
- **Vue Router** with `import.meta.glob` auto-aggregation of
  `router/modules/*.ts`
- Module-isolated views under `src/views/{auth,workbench,admin,analytics}/`
  with their own `api/index.ts`, `components/`, and `hooks/`
- Design tokens from `DESIGN.md` exposed as CSS custom properties in
  `src/assets/design-tokens.css`

### Modules (FDD reference)
| Module | What it does |
|---|---|
| M00 Core | Bootstrap, permission seed, response envelope, ID generation |
| M01 Auth | Enterprise-email login via one-time random password, JWT session |
| M02 Admin | Provider/Model/OpenAPI/User/Role/APIKey-expiry/QuotaPolicy CRUD |
| M03 Workbench | Self-service API-key creation/list/disable/delete, catalog views |
| M04 Gateway | Runtime OpenAI/Anthropic-compatible proxy with quota deduction |
| M05 Analytics | Personal/Ranking/Details/Summary dashboards |

### Background services
The platform expects async workers for email delivery (BS01), outbox dispatch
(BS02), prompt classification (BS03), aggregate precompute (BS04), quota
reset (BS05), cache invalidation (BS06), and DLQ reprocessing (BS07). This
codebase persists outbox events transactionally with each gateway request
(see `TransactionalOutbox` in `backend/app/models/outbox.py`) but does not
ship the worker processes themselves — runtime quota/cost is computed inline
on the request path so the dashboards still work without a worker tier.

## Routes (53 total)

Hit `http://localhost:8000/docs` for the live OpenAPI surface. Headline groups:

```
/api/v1/auth/*              — login, session, refresh, me, logout
/api/v1/admin/*             — providers, models, openapis, users, roles,
                               api-keys (list/extend), quota-reset-policy
/api/v1/workbench/*         — api-keys (CRUD own), models, openapis
/api/v1/gateway/{id}/v1/... — runtime chat/completions & messages
/api/v1/analytics/*         — personal, ranking, prompt-categories,
                               consumption-details, consumption-summary
```

## Generating the typed frontend client

The frontend ships hand-typed stubs under `src/api/generated/` so it can
compile on a clean checkout. Once the backend is running, regenerate the
real client per CLAUDE.md Rule 5 §4:

```bash
cd frontend
npm run openapi:gen
```

That overwrites `src/api/generated/{client.ts,types.ts,services.ts}` from
`http://localhost:8000/openapi.json`.

## Mock provider for local dev

To exercise the gateway without an upstream account, configure a provider
with `api_base_url=mock://local`. `backend/app/services/providers.py`
returns synthetic OpenAI/Anthropic-shaped responses (with realistic token
counts) so cost calculation, quota deduction, and analytics work end-to-end.

## Environment variables (backend)

| Var | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://zqode:zqode_dev@postgres:5432/zqode` | SQLAlchemy URL |
| `JWT_SECRET_KEY` | `dev_change_me` | **Override in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | |
| `ALLOWED_EMAIL_DOMAINS` | `example.com` | CSV, lowercased, e.g. `acme.com,partner.com` |
| `INITIAL_ADMIN_ENTERPRISE_EMAIL` | `admin@example.com` | Bootstrap System Administrator |
| `EMAIL_MODE` | `console` | `console` logs the code; `smtp` emails it |
| `SMTP_HOST` / `SMTP_PORT` | _empty_ / `587` | SMTP relay (required when `EMAIL_MODE=smtp`) |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | _empty_ | SMTP auth credentials |
| `SMTP_FROM` / `SMTP_FROM_NAME` | _empty_ / `ZQode Gateway` | Sender address / display name |
| `SMTP_STARTTLS` / `SMTP_SSL` | `true` / `false` | `587`+STARTTLS, or `465`+SSL |
| `LOGIN_CHALLENGE_EXPIRE_MINUTES` | `5` | |
| `LOGIN_CHALLENGE_MAX_ATTEMPTS` | `5` | |
| `DEFAULT_CURRENCY` | `USD` | |

## Known scope-limits

- BS01–BS07 worker tier is not shipped as separate processes; outbox events
  are written transactionally so a worker can be added later without changing
  the runtime path.
- Provider API keys are stored in `api_key_ciphertext` columns but the
  prototype does not yet encrypt — wire a KMS or libsodium box before
  production rollout.
- Prompt classification (BS03) and analytics aggregation (BS04) are not
  implemented; analytics endpoints query UsageLog/CostRecord directly. The
  `/api/v1/analytics/prompt-categories` endpoint returns an empty list.
- Streaming gateway responses are not implemented (FDD A14 lists this as a
  deferred decision).
- `@hey-api/openapi-ts` generation is wired as `npm run openapi:gen` but the
  initial repo ships hand-typed stubs so a fresh checkout type-checks before
  the backend is reachable; replace by running the script after first boot.
