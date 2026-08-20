# AgentGuard Architecture

## Overview

AgentGuard is built as a **modular monolith** with strong boundaries between modules. This architecture enables:
- Independent module development and testing
- Clear ownership and responsibility
- Easy extraction to microservices if needed
- Stable contracts between modules
- Backward compatibility

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        AgentGuard                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   API Layer (FastAPI)                   │ │
│  │  /api/v1/agents  /api/v1/versions  /api/v1/tools      │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌───────────────────────┴──────────────────────────────┐  │
│  │              Module Layer (Business Logic)            │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│  │
│  │  │    Agent     │  │    Agent     │  │    Tool     ││  │
│  │  │   Registry   │  │  Versioning  │  │  Registry   ││  │
│  │  └──────────────┘  └──────────────┘  └─────────────┘│  │
│  └───────────────────────┬──────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────┴──────────────────────────────┐  │
│  │             Core Platform Layer                       │  │
│  │                                                        │  │
│  │  ┌─────────┐  ┌────────┐  ┌───────┐  ┌───────────┐ │  │
│  │  │Database │  │ Events │  │Config │  │Execution  │ │  │
│  │  └─────────┘  └────────┘  └───────┘  └───────────┘ │  │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│  ┌───────────────────────┴──────────────────────────────┐  │
│  │            Infrastructure Layer                       │  │
│  │                                                        │  │
│  │  ┌──────────┐  ┌────────┐  ┌───────────────────────┐│  │
│  │  │PostgreSQL│  │ Redis  │  │  HTTP Client (SSRF)   ││  │
│  │  └──────────┘  └────────┘  └───────────────────────┘│  │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Module Architecture

Each module follows a layered architecture:

```
Module/
├── interface/          # API routes, request/response handling
├── domain/            # Business entities, domain logic
├── application/       # Use cases, service orchestration
└── infrastructure/    # Database, external services
```

### Layer Responsibilities

**Interface Layer:**
- REST API endpoints
- Request validation
- Response serialization
- HTTP status codes
- OpenAPI documentation

**Domain Layer:**
- Business entities (models)
- Domain logic
- Validation rules
- Domain events

**Application Layer:**
- Use cases
- Service orchestration
- Transaction management
- Event publishing

**Infrastructure Layer:**
- Database repositories
- External API clients
- File system access
- Cache management

## Core Platform

### Database (core/database/)
- SQLAlchemy ORM configuration
- Session management
- Connection pooling
- Migration support (Alembic)

### Events (core/events/)
- Domain event system
- Event publisher/subscriber
- Local event bus (upgradeable to Redis/Kafka)
- Event contracts

### Configuration (core/config/)
- Pydantic Settings
- Environment variable management
- Type-safe configuration
- Per-environment settings

### Execution (core/execution/)
- Execution provider contract
- HTTP execution adapter
- SSRF protection
- Request/response limits
- Timeout enforcement

### Observability (core/observability/)
- Structured logging (structlog)
- Request context binding
- Correlation IDs
- Log levels per environment

## Module Details

### Agent Registry Module

**Purpose:** Manage AI agent definitions

**Tables:** `agents`

**API Endpoints:**
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents` - List agents
- `GET /api/v1/agents/{id}` - Get agent
- `PATCH /api/v1/agents/{id}` - Update agent
- `DELETE /api/v1/agents/{id}` - Archive agent

**Events Emitted:**
- AgentCreated
- AgentUpdated
- AgentDeleted

### Agent Versioning Module

**Purpose:** Immutable agent snapshots

**Tables:** `agent_versions`

**API Endpoints:**
- `POST /api/v1/agents/{id}/versions` - Create version
- `GET /api/v1/agents/{id}/versions` - List versions
- `GET /api/v1/agents/{id}/versions/{vid}` - Get version
- `GET /api/v1/agents/{id}/versions/latest` - Get latest

**Events Emitted:**
- AgentVersionCreated

**Key Features:**
- Immutable snapshots
- Sequential versioning (v1, v2, v3)
- Complete configuration capture
- JSONB storage

### Tool Registry Module

**Purpose:** Tool definitions with risk profiles

**Tables:** `tools`

**API Endpoints:**
- `POST /api/v1/agents/{id}/tools` - Register tool
- `GET /api/v1/agents/{id}/tools` - List tools
- `GET /api/v1/tools/{id}` - Get tool
- `PATCH /api/v1/tools/{id}` - Update tool
- `DELETE /api/v1/tools/{id}` - Archive tool

**Events Emitted:**
- ToolRegistered
- ToolUpdated
- ToolDeleted

**Key Features:**
- JSON Schema validation
- Risk level classification
- Destructive/reversible flags
- Confirmation requirements

## Communication Patterns

### Synchronous (Service Calls)

```python
# Tool Registry verifies agent exists
agent = agent_repository.get_by_id(agent_id)
if not agent:
    raise NotFoundError("Agent", str(agent_id))
```

### Asynchronous (Events)

```python
# Agent Registry publishes event
await event_publisher.publish(
    AgentCreated(
        agent_id=agent.id,
        agent_name=agent.name,
    )
)

# Other modules subscribe
event_publisher.subscribe("agent.created", handle_agent_created)
```

### Foreign Keys (Database)

```sql
CREATE TABLE agent_versions (
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE
);
```

## Security Architecture

### SSRF Protection

**Blocked:**
- Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Localhost (127.0.0.1, ::1, etc.)
- Link-local (169.254.0.0/16)
- Cloud metadata (169.254.169.254)

**Enforced:**
- HTTPS in production
- Request/response size limits
- Timeout limits
- No redirect following

### Authentication & Authorization

*Note: Auth is prepared but not yet implemented in Part 1*

- JWT-based authentication
- Role-based access control (RBAC)
- Workspace isolation
- API key support

### Data Protection

- Secret redaction in logs
- Sensitive field encryption
- Workspace data isolation
- Audit trails

## Data Flow

### Creating an Agent with Tools

```
1. POST /api/v1/agents
   ↓
2. AgentService.create_agent()
   ↓
3. AgentRepository.create()
   ↓
4. Database INSERT
   ↓
5. Publish AgentCreated event
   ↓
6. Return AgentResponse

7. POST /api/v1/agents/{id}/tools
   ↓
8. ToolService.register_tool()
   ↓
9. Verify agent exists (AgentRepository.get_by_id)
   ↓
10. ToolRepository.create()
   ↓
11. Database INSERT
   ↓
12. Publish ToolRegistered event
   ↓
13. Return ToolResponse
```

### Creating a Version Snapshot

```
1. POST /api/v1/agents/{id}/versions
   ↓
2. AgentVersionService.create_version()
   ↓
3. Fetch agent data (AgentRepository.get_by_id)
   ↓
4. Create snapshot (JSONB)
   ↓
5. Generate version number (v1, v2, ...)
   ↓
6. AgentVersionRepository.create()
   ↓
7. Database INSERT
   ↓
8. Publish AgentVersionCreated event
   ↓
9. Return AgentVersionResponse
```

## Scalability Considerations

### Horizontal Scaling

- Stateless API servers
- Database connection pooling
- Event bus for cross-instance communication
- Shared cache (Redis)

### Vertical Scaling

- Database indexes on common queries
- JSONB GIN indexes
- Connection pool sizing
- Query optimization

### Caching Strategy

- Application-level caching
- HTTP response caching
- Database query result caching
- Cache invalidation on writes

## Deployment Architecture

### Development

```
Docker Compose:
- Frontend (Next.js dev server)
- Backend (Uvicorn with reload)
- PostgreSQL
- Redis
```

### Production

```
Kubernetes/Cloud:
- Frontend pods (CDN)
- Backend pods (auto-scaled)
- Managed PostgreSQL (RDS/Cloud SQL)
- Managed Redis (ElastiCache/Cloud Memorystore)
- Load balancer
- TLS termination
```

## Database Schema

See [database-ownership.md](./database-ownership.md) for complete schema.

### Key Tables

- **agents** - Agent definitions
- **agent_versions** - Immutable snapshots
- **tools** - Tool definitions

### Relationships

```
agents (1) ←─── (N) agent_versions (CASCADE)
agents (1) ←─── (N) tools (CASCADE)
```

## Error Handling

### Exception Hierarchy

```
AgentGuardException
├── ValidationError (400)
├── UnauthorizedError (401)
├── ForbiddenError (403)
├── NotFoundError (404)
├── ConflictError (409)
├── RateLimitError (429)
├── InternalError (500)
├── ServiceUnavailableError (503)
├── SecurityError
│   └── SSRFError
└── ExecutionError
```

### Error Response Format

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Agent not found: abc-123",
    "details": {"resource": "Agent", "id": "abc-123"},
    "request_id": "req_xyz"
  }
}
```

## Observability

### Logging

- Structured JSON logs
- Request/correlation IDs
- Log levels: DEBUG, INFO, WARNING, ERROR
- Context binding (user_id, workspace_id, etc.)

### Metrics (Prepared for)

- Request count/duration
- Error rates
- Database query performance
- Event publishing rates

### Tracing (Prepared for)

- Distributed tracing support
- Span creation
- Context propagation

## Testing Strategy

See [testing-strategy.md](./testing-strategy.md) for details.

- **Unit tests** - Isolated component testing
- **Integration tests** - API endpoint testing
- **Contract tests** - Module interface testing
- **E2E tests** - Full workflow testing

## Future Enhancements (Part 2+)

- Scenario generation engine
- Execution orchestration
- Trace capture and analysis
- Evaluation with LLM-as-a-Judge
- Failure classification
- Reliability scoring
- Regression detection
- Automated recommendations
- Reporting and dashboards
- Scheduled evaluations
- Notification system
- Team/workspace management
- Browser automation support
- CI/CD integration for external users

## References

- [Module Boundaries](./module-boundaries.md)
- [Database Ownership](./database-ownership.md)
- [Git Workflow](./git-workflow.md)
- [API Contracts](./api-contracts.md)
- [Security Model](./security.md)
- [Testing Strategy](./testing-strategy.md)
