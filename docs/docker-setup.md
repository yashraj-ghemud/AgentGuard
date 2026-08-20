# Docker Setup Guide

Complete guide for running AgentGuard with Docker Compose.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Docker version 20.10+
- Docker Compose version 2.0+

## Quick Start

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database)
docker-compose down -v
```

## Service Architecture

```
┌─────────────────┐
│   Frontend      │  Port 3000
│   (Next.js)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Backend       │  Port 8000
│   (FastAPI)     │
└────┬────────┬───┘
     │        │
     ↓        ↓
┌─────────┐ ┌──────┐
│PostgreSQL│ │Redis │
│Port 5432 │ │Port  │
└──────────┘ │6379  │
             └──────┘
```

## Services

### PostgreSQL
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Database**: agentguard
- **User**: agentguard
- **Password**: agentguard
- **Volume**: postgres_data

**Health Check**: Runs `pg_isready` every 10s

### Redis
- **Image**: redis:7-alpine
- **Port**: 6379
- **Volume**: redis_data

**Health Check**: Runs `redis-cli ping` every 10s

### Backend (FastAPI)
- **Build**: ./Backend/Dockerfile
- **Port**: 8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

**Environment Variables**:
- `DATABASE_URL`: postgresql://agentguard:agentguard@postgres:5432/agentguard
- `REDIS_URL`: redis://redis:6379/0

**Depends On**: PostgreSQL (healthy), Redis (healthy)

### Frontend (Next.js)
- **Build**: ./Frontend/Dockerfile
- **Port**: 3000
- **URL**: http://localhost:3000

**Environment Variables**:
- `NEXT_PUBLIC_API_URL`: http://localhost:8000

**Depends On**: Backend

## First-Time Setup

### 1. Create .env file

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql://agentguard:agentguard@postgres:5432/agentguard

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# LLM Provider (for Part 2+)
OPENAI_API_KEY=your-api-key-here
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up --build -d

# Wait for health checks to pass
docker-compose ps
```

### 3. Run Database Migration

```bash
# Run Alembic migrations
docker-compose exec backend alembic upgrade head
```

### 4. Seed Sample Data (Optional)

```bash
# Load demo agents and tools
docker-compose exec backend python scripts/seed_data.py
```

### 5. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs

# Check frontend
open http://localhost:3000
```

## Development Workflow

### Hot Reload

Both backend and frontend support hot reload:

- **Backend**: Changes to `./Backend` trigger auto-reload
- **Frontend**: Changes to `./Frontend` trigger hot module replacement

### Run Commands Inside Containers

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# PostgreSQL client
docker-compose exec postgres psql -U agentguard -d agentguard

# Redis client
docker-compose exec redis redis-cli
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restart Services

```bash
# Restart specific service
docker-compose restart backend

# Restart all
docker-compose restart
```

## Database Management

### Create Migration

```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Run Migrations

```bash
docker-compose exec backend alembic upgrade head
```

### Rollback Migration

```bash
docker-compose exec backend alembic downgrade -1
```

### Database Backup

```bash
# Export database
docker-compose exec postgres pg_dump -U agentguard agentguard > backup.sql

# Restore database
docker-compose exec -T postgres psql -U agentguard agentguard < backup.sql
```

### Reset Database

```bash
# Stop services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Restart
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Reseed data
docker-compose exec backend python scripts/seed_data.py
```

## Testing Inside Containers

### Backend Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=. --cov-report=html

# Run specific test file
docker-compose exec backend pytest tests/test_example.py

# Run with verbose output
docker-compose exec backend pytest -v
```

### Frontend Tests

```bash
# Run tests
docker-compose exec frontend npm test

# Type check
docker-compose exec frontend npm run type-check

# Lint
docker-compose exec frontend npm run lint
```

## Troubleshooting

### Services Won't Start

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs

# Check Docker resources
docker system df

# Prune unused resources
docker system prune -a
```

### Port Conflicts

If ports 3000, 5432, 6379, or 8000 are in use:

1. Edit `docker-compose.yml`
2. Change port mappings (e.g., `"8001:8000"`)
3. Update `.env` configuration
4. Restart services

### Database Connection Issues

```bash
# Verify PostgreSQL is healthy
docker-compose exec postgres pg_isready -U agentguard

# Check logs
docker-compose logs postgres

# Verify connection string in .env
grep DATABASE_URL .env
```

### Frontend Can't Reach Backend

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check frontend environment
docker-compose exec frontend printenv | grep API_URL

# Verify CORS settings in Backend/.env
```

### Hot Reload Not Working

```bash
# Restart with fresh build
docker-compose down
docker-compose up --build

# Check volume mounts
docker-compose config
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove all unused resources
docker system prune -a --volumes
```

## Production Considerations

⚠️ **This docker-compose.yml is for DEVELOPMENT ONLY**

For production deployment:

1. **Remove volume mounts** - Use built images
2. **Use secrets management** - Not environment variables
3. **Configure reverse proxy** - Nginx or Traefik
4. **Enable HTTPS** - Use Let's Encrypt
5. **Set production environment** - `ENV=production`
6. **Use managed databases** - RDS, Cloud SQL, etc.
7. **Configure resource limits** - Memory and CPU
8. **Set up monitoring** - Prometheus, Grafana
9. **Enable backups** - Automated database backups
10. **Use multi-stage builds** - Optimize image sizes

## Performance Tuning

### Increase PostgreSQL Resources

Edit `docker-compose.yml`:

```yaml
postgres:
  # ... existing config
  command: postgres -c shared_buffers=256MB -c max_connections=200
```

### Increase Backend Workers

```yaml
backend:
  # ... existing config
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Production Build

```yaml
frontend:
  # ... existing config
  command: npm run build && npm run start
```

## Network Configuration

Services communicate via Docker internal network:

- `postgres:5432` - PostgreSQL hostname from backend
- `redis:6379` - Redis hostname from backend
- `backend:8000` - Backend hostname from frontend
- `localhost:8000` - Backend from host machine
- `localhost:3000` - Frontend from host machine

## Volume Management

### Persistent Volumes

- `postgres_data` - PostgreSQL database files
- `redis_data` - Redis persistence files

### List Volumes

```bash
docker volume ls | grep agentguard
```

### Inspect Volume

```bash
docker volume inspect agentguard_postgres_data
```

### Backup Volume

```bash
docker run --rm -v agentguard_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Health Checks

All services include health checks:

```bash
# Check health status
docker-compose ps

# Manual health check - PostgreSQL
docker-compose exec postgres pg_isready -U agentguard

# Manual health check - Redis
docker-compose exec redis redis-cli ping

# Manual health check - Backend
curl http://localhost:8000/health
```

## Environment Variables Reference

| Variable | Service | Default | Description |
|----------|---------|---------|-------------|
| `POSTGRES_USER` | postgres | agentguard | Database user |
| `POSTGRES_PASSWORD` | postgres | agentguard | Database password |
| `POSTGRES_DB` | postgres | agentguard | Database name |
| `DATABASE_URL` | backend | postgresql://... | Full database connection string |
| `REDIS_URL` | backend | redis://... | Redis connection string |
| `NEXT_PUBLIC_API_URL` | frontend | http://localhost:8000 | Backend API URL |

## Next Steps

After Docker setup:

1. **Explore API** - http://localhost:8000/docs
2. **View Frontend** - http://localhost:3000
3. **Review Logs** - `docker-compose logs -f`
4. **Run Tests** - `docker-compose exec backend pytest`
5. **Seed Data** - `docker-compose exec backend python scripts/seed_data.py`

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify health: `docker-compose ps`
3. Review troubleshooting section above
4. Check GitHub issues
5. Review architecture documentation in `docs/`
