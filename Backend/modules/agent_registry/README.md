# Agent Registry Module

## Purpose

The Agent Registry module manages AI agent definitions, configurations, and metadata. It provides CRUD operations for agents and serves as the foundation for versioning, testing, and evaluation.

## Responsibilities

- **Agent Creation** - Register new AI agents with configuration
- **Agent Retrieval** - Fetch agent details by ID or list all agents
- **Agent Updates** - Modify agent configuration and metadata
- **Agent Archival** - Soft delete agents (maintain history)
- **Validation** - Ensure agent configurations are valid
- **Event Publishing** - Publish domain events for agent lifecycle

## Non-Responsibilities

- Agent execution (handled by Execution Engine)
- Version management (handled by Agent Versioning module)
- Tool definitions (handled by Tool Registry module)
- Scenario generation (handled by Scenario Engine)
- Evaluation (handled by Evaluation Engine)

## Public Interfaces

### REST API

```
POST   /api/v1/agents          - Create agent
GET    /api/v1/agents          - List agents (paginated)
GET    /api/v1/agents/{id}     - Get agent by ID
PATCH  /api/v1/agents/{id}     - Update agent
DELETE /api/v1/agents/{id}     - Archive agent
```

### Service Interface

```python
class AgentService:
    async def create_agent(create_request: CreateAgentRequest) -> Agent
    async def get_agent(agent_id: UUID) -> Agent
    async def list_agents(filters: AgentFilters, pagination: PaginationParams) -> PaginatedResponse[Agent]
    async def update_agent(agent_id: UUID, update_request: UpdateAgentRequest) -> Agent
    async def archive_agent(agent_id: UUID) -> None
```

## Inputs

### CreateAgentRequest
- `name` (string, required) - Agent name
- `description` (string, optional) - Agent description
- `endpoint_url` (string, required) - Agent execution endpoint
- `execution_mode` (enum, required) - http, sdk, browser
- `purpose` (string, optional) - Agent purpose/use case
- `risk_profile` (object, optional) - Risk configuration
- `metadata` (dict, optional) - Additional metadata
- `workspace_id` (UUID, optional) - Workspace ownership

### UpdateAgentRequest
- All fields optional, only provided fields are updated

### AgentFilters
- `name` (string, optional) - Filter by name (partial match)
- `execution_mode` (enum, optional) - Filter by execution mode
- `status` (enum, optional) - Filter by status
- `workspace_id` (UUID, optional) - Filter by workspace

## Outputs

### Agent
- `id` (UUID) - Unique identifier
- `name` (string) - Agent name
- `description` (string) - Agent description
- `endpoint_url` (string) - Execution endpoint
- `execution_mode` (enum) - Execution mode
- `purpose` (string) - Agent purpose
- `status` (enum) - active, inactive, archived
- `risk_profile` (object) - Risk configuration
- `metadata` (dict) - Additional metadata
- `workspace_id` (UUID) - Workspace ID
- `created_at` (datetime) - Creation timestamp
- `updated_at` (datetime) - Last update timestamp

## Dependencies

### Core Dependencies
- `core.database` - Database session management
- `core.events` - Event publishing
- `shared.types` - Common types (pagination, results)
- `shared.exceptions` - Exception types

### External Dependencies
- SQLAlchemy - Database ORM
- Pydantic - Validation

## Events Emitted

- `AgentCreated` - When new agent is created
- `AgentUpdated` - When agent is modified
- `AgentDeleted` - When agent is archived

## Events Consumed

None (this module does not consume events)

## Database Entities Owned

### agents table
- `id` (UUID, PK)
- `name` (VARCHAR(255), NOT NULL)
- `description` (TEXT)
- `endpoint_url` (TEXT, NOT NULL)
- `execution_mode` (VARCHAR(50), NOT NULL)
- `purpose` (TEXT)
- `status` (VARCHAR(50), NOT NULL, DEFAULT 'active')
- `risk_profile` (JSONB)
- `metadata` (JSONB)
- `workspace_id` (UUID, NULLABLE)
- `created_at` (TIMESTAMP, NOT NULL)
- `updated_at` (TIMESTAMP, NOT NULL)

Indexes:
- `idx_agents_name` - For name searches
- `idx_agents_status` - For status filtering
- `idx_agents_workspace_id` - For workspace filtering

## Validation Rules

### Agent Name
- Required
- 1-255 characters
- Must be unique within workspace (if workspace_id provided) or globally
- Alphanumeric, spaces, hyphens, underscores allowed

### Endpoint URL
- Required
- Must be valid URL format
- HTTPS required in production
- Subject to SSRF validation (handled by execution layer)

### Execution Mode
- Required
- Must be one of: http, sdk, browser
- Immutable after creation (create new version instead)

### Risk Profile
- Optional
- If provided, must contain valid risk_level (low, medium, high, critical)
- Must contain valid boolean flags (requires_human_approval, etc.)

## Extension Points

### Custom Validators
Additional validators can be registered for specific agent types or use cases.

### Event Handlers
External systems can subscribe to agent events for notifications, logging, or workflow triggers.

### Storage Backend
The repository interface can be swapped to use different storage (though PostgreSQL is primary).

## Test Strategy

### Unit Tests
- Domain model validation
- Service business logic
- Repository queries

### Integration Tests
- Full API request/response cycle
- Database persistence
- Event publishing

### Contract Tests
- API request/response schemas
- Service interface contracts
- Event schemas

## Security Considerations

- Endpoint URLs are validated but not executed by this module
- SSRF protection applied at execution time
- Sensitive data in metadata should be encrypted at rest
- Workspace isolation enforced at query level
- Authentication required (enforced by API layer)

## Performance Considerations

- List queries use pagination by default
- Indexes on commonly filtered fields
- No N+1 queries (use eager loading where needed)
- Soft deletes maintain data lineage

## Module Isolation

This module:
- MUST NOT directly access other module's database tables
- MUST NOT import implementation details from other modules
- MUST communicate with other modules through events or service interfaces
- SHOULD remain functional even if other modules are unavailable
