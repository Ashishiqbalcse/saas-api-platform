# 🚀 SaaS API Platform with Full Monetization Stack

A production-ready, multi-tenant SaaS API Platform built with **FastAPI, PostgreSQL, Redis, React, Docker, Stripe, Prometheus, Grafana, and GitHub Actions**.

The platform provides secure API key authentication, tenant isolation, usage analytics, billing automation, observability, and CI/CD deployment pipelines suitable for modern SaaS businesses.

---

## ✨ Key Features

### 🔐 Authentication & Security

* API Key Authentication
* HMAC-SHA256 Key Hashing
* Secure Key Storage
* Tenant Isolation
* Row-Level Security (RLS)
* Authorization Middleware

### ⚡ API Management

* Multi-Tenant Architecture
* API Key Lifecycle Management
* Rate Limiting with Redis
* Plan-Based Access Control
* Usage Tracking & Analytics
* Request Logging

### 💳 Billing & Monetization

* Stripe Checkout Integration
* Stripe Customer Portal
* Webhook Verification
* Subscription Management
* Free / Pro / Enterprise Plans

### 📊 Monitoring & Observability

* Prometheus Metrics
* Grafana Dashboards
* API Latency Tracking
* Error Monitoring
* Tenant Usage Analytics
* Active Tenant Metrics

### 🚀 DevOps & Deployment

* Docker Compose
* Nginx Reverse Proxy
* GitHub Actions CI/CD
* AWS ECR Integration
* EC2 Rolling Deployment
* Automated Testing Pipeline

---

## 🏗 Architecture

```text
                    ┌─────────────┐
                    │ React Frontend │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Nginx    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    └───┬─────┬───┘
                        │     │
                        ▼     ▼
                ┌─────────┐ ┌──────────┐
                │ Redis   │ │PostgreSQL│
                └─────────┘ └──────────┘
                        │
                        ▼
                  Rate Limiting

        Prometheus ─────► Grafana

        Stripe ─────────► Billing System
```

---

## 🛠 Tech Stack

## Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* Redis
* Alembic
* Celery

## Frontend

* React
* Vite
* JavaScript
* CSS

## Billing

* Stripe API
* Stripe Checkout
* Stripe Customer Portal

## Monitoring

* Prometheus
* Grafana

## DevOps

* Docker
* Docker Compose
* GitHub Actions
* AWS EC2
* AWS ECR
* Nginx

---

## 📦 Project Structure

```text
backend/
│
├── app/
│   ├── api/
│   ├── auth/
│   ├── billing/
│   ├── db/
│   ├── monitoring/
│   ├── ratelimit/
│   └── usage/
│
├── alembic/
└── tests/

frontend/
│
└── src/

grafana/
prometheus/
nginx/

.github/workflows/

docker-compose.yml
```

---

## ⚙️ Local Development Setup

## 1. Clone Repository

```bash
git clone https://github.com/Ashishiqbalcse/saas-api-platform.git
cd saas-api-platform
```

## 2. Configure Environment

```bash
cp .env.example .env
```

## 3. Start Services

```bash
docker compose up --build -d
```

## 4. Run Database Migration

```bash
docker compose exec backend alembic upgrade head
```

---

## 🧪 Testing

Run all tests:

```bash
pytest -v
```

Current Status:

```text
7 Tests Passing ✅
```

Covered Areas:

* Security
* API Keys
* Rate Limiting
* Stripe Webhooks
* Health Checks

---

## 📈 Monitoring

## Prometheus

```text
http://localhost:9090
```

Metrics:

* Request Count
* Request Latency
* Error Rate
* Active Tenants
* Rate Limit Hits

## Grafana

```text
http://localhost:3001
```

Default Login:

```text
Username: admin
Password: changeme
```

Dashboard Includes:

* P50 Latency
* P95 Latency
* Error Rate
* API Usage
* Endpoint Analytics
* Tenant Metrics

---

## 🔌 API Endpoints

## Public Endpoints

| Method | Endpoint              | Description        |
| ------ | --------------------- | ------------------ |
| GET    | /health               | Health Check       |
| POST   | /api/tenants/register | Register Tenant    |
| POST   | /api/billing/webhook  | Stripe Webhook     |
| GET    | /metrics              | Prometheus Metrics |

## Protected Endpoints

| Method | Endpoint              |
| ------ | --------------------- |
| GET    | /api/v1/health/authed |
| POST   | /api/v1/analyze       |
| POST   | /api/v1/summarize     |
| GET    | /api/v1/models        |
| GET    | /api/keys             |
| POST   | /api/keys             |
| DELETE | /api/keys/{id}        |
| GET    | /api/usage/summary    |
| GET    | /api/usage/daily      |
| GET    | /api/usage/endpoints  |

---

## 💳 Subscription Plans

| Plan       | Daily Requests |
| ---------- | -------------- |
| Free       | 100            |
| Pro        | 10,000         |
| Enterprise | Unlimited      |

---

## 🚀 Production Deployment

Required GitHub Secrets:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
ECR_REGISTRY
EC2_HOST
EC2_SSH_KEY
PRODUCTION_API_URL
```

Deployment Pipeline:

```text
Git Push
    ↓
GitHub Actions
    ↓
Run Tests
    ↓
Build Docker Images
    ↓
Push to AWS ECR
    ↓
Deploy to EC2
    ↓
Rolling Update via Nginx
```

---

## 📸 Screenshots

Add screenshots here:

* Dashboard
* Grafana
* Prometheus
* Swagger Docs

```text
docs/screenshots/
```

---

## 👨‍💻 Author

Ashish Iqbal

B.Tech CSE (2022–2026)

Assam Kaziranga University

GitHub:
[https://github.com/Ashishiqbalcse]

---

## ⭐ Project Highlights

✅ Multi-Tenant SaaS Architecture

✅ API Key Authentication

✅ Redis Rate Limiting

✅ Stripe Billing

✅ React Dashboard

✅ Prometheus Monitoring

✅ Grafana Visualization

✅ Dockerized Infrastructure

✅ CI/CD Automation

✅ Production Deployment Ready
