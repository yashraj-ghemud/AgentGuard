# Docker Setup Guide

This guide runs AgentGuard locally with Docker Compose. The compose stack is for development and local testing, not production deployment.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Docker version 20.10+
- Docker Compose version 2+

## Quick Start

```bash
docker-compose up --build -d
docker-compose ps
docker-compose logs -f
docker-compose down
```

Use `docker-compose down -v` only when you intentionally want to delete the local PostgreSQL/Redis volumes.

## Service Architecture

```text
Frontend (Next.js :3000)
        |
        v
Backend (FastAPI :8000)
     /        \
PostgreSQL    Redis
 :5432        :6379
```

## First-Time Setup

### 1. Create local environment configuration

```bash
cp .env.example .env
```

Set real local secrets/API credentials where required. Never commit `.env` or production credentials.

### 2. Start services

```bash
docker-compose up --build -d
docker-compose ps
```

### 3. Run database migrations

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Optional: seed one local development agent

AgentGuard no longer ships hardcoded fake production agents or public example endpoints. The seed script requires an HTTP endpoint that you control:

```bash
docker-compose exec backend bash
export SEED_AGENT_ENDPOINT="http://host.docker.internal:9000/run"
export SEED_AGENT_NAME="My Local Test Agent"
python scripts/seed_data.py
```

The script creates one clearly marked development record. It does not invent production releases, real customers, or public URLs.

### 5. Verify

```bash
curl http://localhost:8000/health
```

Open `http://localhost:8000/docs` for the API and `http://localhost:3000` for the frontend.

## Grounding / Hallucination Demo

For an immediate, provider-independent demonstration, open the frontend **Grounding Check** page and supply:

1. The actual answer produced by the model under test.
2. Trusted reference evidence (retrieved document, policy text, database result, etc.).
3. Optional required facts and forbidden claims.
4. Whether the evidence is expected to be sufficient to answer.

The checker reports unsupported sentences, missing required facts, forbidden claims, and missing abstention. It is a transparent evidence-support heuristic, not a proof of real-world truth.

The API equivalent is:

```http
POST /api/v1/evaluations/grounding
```

## Development Workflow

### Backend shell

```bash
docker-compose exec backend bash
```

### Frontend shell

```bash
docker-compose exec frontend sh
```

### Logs

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restart

```bash
docker-compose restart backend
docker-compose restart frontend
```

## Database Management

```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic downgrade -1
```

Backup:

```bash
docker-compose exec postgres pg_dump -U agentguard agentguard > backup.sql
```

## Testing

### Backend

```bash
docker-compose exec backend pytest
```

For the new grounding checks specifically:

```bash
docker-compose exec backend pytest tests/test_grounding.py -v
```

### Frontend

```bash
docker-compose exec frontend npm run type-check
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run build
```

## Troubleshooting

### Port conflicts

Change the host-side mappings in `docker-compose.yml` and update `NEXT_PUBLIC_API_URL` for the frontend if needed.

### Database connection issues

```bash
docker-compose exec postgres pg_isready -U agentguard
docker-compose logs postgres
```

### Frontend cannot reach backend

```bash
curl http://localhost:8000/health
docker-compose exec frontend printenv | grep API_URL
```

### Reset the local database

```bash
docker-compose down -v
docker-compose up --build -d
docker-compose exec backend alembic upgrade head
```

Run the seed script again only with `SEED_AGENT_ENDPOINT` explicitly configured.

## Production Boundary

This compose file is for local development. Production requires a separately managed deployment with HTTPS, secret management, controlled networking, resource limits, backups, and monitored databases.
