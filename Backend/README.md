# AgentGuard Backend

FastAPI-based backend for AgentGuard platform with modular architecture.

## Architecture

The backend follows a modular monolith pattern with clear boundaries:

```
Backend/
├── core/                    # Core platform services
│   ├── database/           # Database configuration and session management
│   ├── auth/               # Authentication and authorization
│   ├── config/             # Application configuration
│   ├── events/             # Event bus and domain events
│   └── observability/      # Logging, metrics, tracing
├── modules/                 # Feature modules
│   ├── agent_registry/     # Agent CRUD operations
│   │   ├── interface/      # API routes and contracts
│   │   ├── domain/         # Domain models and logic
│   │   ├── application/    # Application services
│   │   ├── infrastructure/ # Database repositories
│   │   └── tests/          # Module-specific tests
│   ├── agent_versioning/   # Immutable agent versions
│   └── tool_registry/      # Tool definitions and registry
├── shared/                  # Shared utilities and types
│   ├── types/              # Common type definitions
│   ├── utils/              # Utility functions
│   └── exceptions/         # Custom exceptions
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── contract/           # Contract tests
│   └── fixtures/           # Test fixtures and factories
├── alembic/                 # Database migrations
└── scripts/                 # Utility scripts
```

## Module Structure

Each module follows a layered architecture:

- **Interface Layer** - API routes, request/response models, validation
- **Domain Layer** - Business logic, domain models, domain events
- **Application Layer** - Use cases, service orchestration
- **Infrastructure Layer** - Database access, external services

## Setup

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set up environment
cp ../.env.example ../.env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

### With Docker

```bash
# From project root
make dev
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=modules --cov=shared

# Run specific test file
pytest tests/unit/test_agent_registry.py

# Run integration tests only
pytest tests/integration
```

## Code Quality

```bash
# Linting
ruff check .

# Formatting
black .

# Type checking
mypy core modules shared
```

## API Documentation

When the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Module Development

To create a new module:

1. Create module directory structure:
```bash
mkdir -p modules/new_module/{interface,domain,application,infrastructure,tests}
```

2. Define module contract in `README.md`
3. Implement domain models
4. Create application services
5. Add infrastructure adapters
6. Write tests
7. Create API routes

See [Module Boundaries](../../docs/module-boundaries.md) for details.

## Database Ownership

Each module owns specific tables:

- **agent_registry**: `agents`
- **agent_versioning**: `agent_versions`
- **tool_registry**: `tools`, `agent_tools`

Cross-module data access must go through service interfaces.

## Events

Modules communicate through domain events:

- `AgentCreated`
- `AgentUpdated`
- `AgentVersionCreated`
- `ToolRegistered`

See `core/events/` for event definitions.

## Security

The backend implements:
- SSRF protection
- Private network blocking
- Request/response size limits
- Timeout enforcement
- Input validation
- Secret redaction

See [Security Documentation](../../docs/security.md) for details.

## Troubleshooting

### Database connection errors
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure migrations are applied

### Import errors
- Ensure virtual environment is activated
- Verify all dependencies are installed
- Check PYTHONPATH includes project root

### Test failures
- Check test database is available
- Ensure test fixtures are up to date
- Review test logs for specific errors
