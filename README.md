# AgentGuard

**Automated Red-Teaming & Reliability Engineering for AI Agents**

AgentGuard is a production-grade platform for testing, validating, and improving the reliability of AI agents through automated red-teaming, scenario generation, execution monitoring, and regression detection.

## Architecture

AgentGuard follows a **modular monolith** architecture with strong boundaries between modules. Each module owns its domain, exposes clear contracts, and communicates through well-defined interfaces.

### Core Principles

1. **Module Independence** - Modules can be developed, tested, and deployed independently
2. **Stable Contracts** - Public interfaces remain backward compatible
3. **Database Ownership** - Each module owns its tables; cross-module access through services only
4. **Event-Driven** - Modules communicate through domain events
5. **Provider Abstraction** - Business logic decoupled from vendor implementations

## Project Structure

```
AgentGuard/
├── Backend/               # Python FastAPI backend
│   ├── core/             # Core platform (database, auth, config, events)
│   ├── modules/          # Feature modules
│   │   ├── agent_registry/
│   │   ├── agent_versioning/
│   │   ├── tool_registry/
│   │   └── [future modules]/
│   ├── shared/           # Shared types and utilities
│   └── tests/            # Test suite
├── Frontend/             # Next.js frontend
│   ├── src/
│   │   ├── modules/      # Feature-specific UI modules
│   │   ├── core/         # Core UI components
│   │   └── lib/          # Utilities and API clients
├── docs/                 # Architecture and module documentation
└── .github/              # CI/CD workflows
```

## Modules

### Part 1 - Foundation (Current)

- **MODULE 00** - Core Platform (database, auth, events, config)
- **MODULE 01** - Agent Registry (CRUD for AI agents)
- **MODULE 02** - Agent Versioning (immutable version snapshots)
- **MODULE 03** - Tool Registry (tool definitions with risk profiles)

### Part 2 - Scenario Intelligence

- **MODULE 04** - Agent Intelligence Engine
- **MODULE 05** - Risk Analysis Engine
- **MODULE 06** - Test Strategy Planner
- **MODULE 07** - Scenario Generation Engine

### Part 3 - Execution and Reliability

- **MODULE 08** - Safe HTTP Execution Provider
- **MODULE 09** - Deterministic Evaluation Engine
- **MODULE 10** - Reliability Scoring Engine
- **MODULE 11** - Regression Detection Engine

### Future Advanced Features

- **MODULE 12** - Sandbox Engine
- **MODULE 13** - Trace Engine
- **MODULE 14** - Failure Classification Expansion
- **MODULE 15** - Recommendation Engine
- **MODULE 16** - Reporting Engine
- **MODULE 17** - Scheduling Engine
- **MODULE 18** - Browser Agent Adapter
- **MODULE 19** - CI/CD Integration
- **MODULE 20** - Notification System
- **MODULE 21** - Workspace / Team Management

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd AgentGuard

# Start all services
make dev

# Run tests
make test

# Run one scenario through the evaluation API after starting the backend
# See docs/evaluation.md for the full request contract and regression workflow

# Run linting
make lint

# Run type checking
make typecheck
```

### Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Application secret key
- `ENCRYPTION_KEY` - Data encryption key

See `.env.example` for full list.

## Git Workflow

AgentGuard uses a strict branch-based workflow to maintain stability:

- **main** - Production-ready code, always stable
- **integration** - Integration testing before main merge
- **feature/** - Feature development branches
- **fix/** - Bug fix branches
- **hotfix/** - Urgent production fixes

See [docs/git-workflow.md](docs/git-workflow.md) for details.

## Testing

```bash
# Backend tests
cd Backend
pytest

# Frontend tests
cd Frontend
npm test

# Integration tests
make test-integration

# Contract tests
make test-contracts
```

## API Documentation

API documentation is available at:
- Development: http://localhost:8000/docs
- Staging: https://staging-api.agentguard.io/docs

See [docs/api-contracts.md](docs/api-contracts.md) for API specifications.

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Module Boundaries](docs/module-boundaries.md)
- [Git Workflow](docs/git-workflow.md)
- [API Contracts](docs/api-contracts.md)
- [Database Ownership](docs/database-ownership.md)
- [Security Model](docs/security.md)
- [Testing Strategy](docs/testing-strategy.md)
- [Development Roadmap](docs/roadmap.md)
- [Execution and Evaluation Workflow](docs/evaluation.md)

## Security

AgentGuard implements multiple security layers:
- SSRF protection
- Private network blocking
- Request/response size limits
- Timeout enforcement
- Secret redaction
- Input validation

See [docs/security.md](docs/security.md) for details.

## Contributing

1. Create a feature branch from `main`
2. Implement changes with tests
3. Ensure all CI checks pass
4. Create pull request to `integration`
5. After integration tests pass, merge to `main`

## License

[License details to be added]

## Support

[Support information to be added]
