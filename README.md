# SaaS API Platform

A production-oriented, multi-tenant API platform with API key auth, hashed key storage, tenant-scoped PostgreSQL access, Redis rate limiting, usage tracking, Stripe billing, a React developer dashboard, Prometheus metrics, Grafana dashboards, Docker Compose, and GitHub Actions deployment to AWS EC2/ECR.

## Architecture

```text
Client request with Authorization: Bearer sk_live_...
  -> Auth middleware validates hashed API key and resolves tenant
  -> Redis rate limiter enforces plan limits atomically
  -> FastAPI route handler runs tenant-scoped product logic
  -> PostgreSQL stores tenant data behind RLS policies
  -> Usage event logger records endpoint, latency, status, tokens
  -> Prometheus exports request, latency, error, and rate-limit metrics
  -> Stripe webhooks update tenant billing plan and payment status
```

## Core Features

- Multi-tenant data model with PostgreSQL Row Level Security policies in `backend/alembic/versions/0001_initial_platform.py`.
- API key lifecycle: generate, list, rotate by creating a new key, and revoke. Raw keys are shown once; only HMAC-SHA256 hashes are stored.
- Redis atomic daily limits using a Lua script with `INCR` and `EXPIRE` in one operation.
- Plan limits: Free `100/day`, Pro `10,000/day`, Enterprise unlimited.
- Usage table records `tenant_id`, `endpoint`, `latency_ms`, `status_code`, and `tokens_used`.
- Stripe Checkout, Customer Portal, and signed webhook verification.
- React dashboard for usage graphs, endpoint stats, API keys, and billing.
- Prometheus `/metrics` and a provisioned Grafana dashboard for p50/p95 latency, errors, top endpoints per tenant, and rate-limit hits.
- GitHub Actions pipeline: lint, test, frontend build, Docker build, push to ECR, and EC2 rolling update behind Nginx.

## Local Setup

1. Copy environment values:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build -d
```

3. Run migrations:

```bash
docker compose exec backend alembic upgrade head
```

4. Register a tenant and save the returned API key:

```bash
curl -X POST http://localhost:8000/api/tenants/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Tenant","email":"demo@example.com"}'
```

5. Call an authenticated product endpoint:

```bash
curl http://localhost:8000/api/v1/health/authed \
  -H "Authorization: Bearer sk_live_YOUR_KEY"
```

6. Open the services:

- Developer dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001, default `admin / changeme`

## Stripe Webhooks In Development

Use the Stripe CLI against the local Nginx API entrypoint:

```bash
stripe listen --forward-to localhost:8000/api/billing/webhook
```

Copy the printed `whsec_...` signing secret into `.env` as `STRIPE_WEBHOOK_SECRET`.

The repository includes a webhook signature test in `backend/tests/test_stripe_webhook.py`; keep it passing before changing billing code.

## API Routes

Public routes:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/api/tenants/register` | Create a free tenant and first API key |
| `POST` | `/api/billing/webhook` | Stripe webhook receiver |
| `GET` | `/metrics` | Prometheus metrics |

Authenticated routes:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health/authed` | Verify API key and tenant context |
| `POST` | `/api/v1/analyze` | Example product endpoint |
| `POST` | `/api/v1/summarize` | Pro+ example product endpoint |
| `GET` | `/api/v1/models` | Plan-gated model list |
| `GET` | `/api/keys` | List active API keys |
| `POST` | `/api/keys` | Create a new API key |
| `DELETE` | `/api/keys/{key_id}` | Revoke an API key |
| `GET` | `/api/usage/summary` | Current plan and daily usage |
| `GET` | `/api/usage/daily` | Daily usage for charts |
| `GET` | `/api/usage/endpoints` | Top endpoints for the dashboard |
| `POST` | `/api/billing/checkout` | Create Stripe Checkout session |
| `POST` | `/api/billing/portal` | Open Stripe billing portal |

## Project Structure

```text
backend/
  app/
    api/          FastAPI route modules
    auth/         API key auth and tenant resolution
    billing/      Stripe plans, checkout, portal, webhooks
    db/           SQLAlchemy session and Redis client
    monitoring/   Prometheus metrics
    ratelimit/    Redis atomic daily limiter
    usage/        usage event middleware and reporting routes
  alembic/        migrations, including RLS policies
  tests/          focused backend tests
frontend/
  src/            Vite React developer dashboard
grafana/          provisioned datasource and dashboard JSON
prometheus/       scrape config
nginx/            API reverse proxy for local and EC2 rolling deploys
.github/workflows/deploy.yml
docker-compose.yml
```

## Production Deploy Notes

Create ECR repositories:

```bash
aws ecr create-repository --repository-name saas-api-platform --region ap-south-1
aws ecr create-repository --repository-name saas-frontend --region ap-south-1
```

Required GitHub Actions secrets:

| Secret | Purpose |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | ECR push credentials |
| `AWS_SECRET_ACCESS_KEY` | ECR push credentials |
| `ECR_REGISTRY` | Example: `123456789.dkr.ecr.ap-south-1.amazonaws.com` |
| `EC2_HOST` | EC2 public DNS or IP |
| `EC2_SSH_KEY` | Private SSH key for the `ubuntu` user |
| `PRODUCTION_API_URL` | Public API URL used when building the frontend |

On the EC2 instance, clone the repo to `/app/saas-api-platform`, create `.env`, install Docker, and run:

```bash
docker compose up -d
docker compose exec backend alembic upgrade head
```

After that, pushes to `main` run the CI/CD workflow and deploy new images through the Nginx-backed rolling update.
