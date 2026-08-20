# Agent Versioning Module

## Purpose

The Agent Versioning module manages immutable snapshots of agent configurations at specific points in time. This enables regression detection, historical comparison, and reliable testing against known configurations.

## Responsibilities

- **Version Creation** - Create immutable snapshots of agent configurations
- **Version Retrieval** - Fetch version details and history
- **Version Listing** - List versions for an agent
- **Snapshot Integrity** - Ensure versions remain immutable after creation
- **Automatic Versioning** - Generate version numbers and track lineage

## Non-Responsibilities

- Agent CRUD operations (handled by Agent Registry)
- Version execution (handled by Execution Engine)
- Version comparison/diff (handled by future Regression Engine)
- Tool definitions (handled by Tool Registry)
- Evaluation results (handled by Evaluation Engine)

## Public Interfaces

### REST API

```
POST   /api/v1/agents/{agent_id}/versions       - Create version snapshot
GET    /api/v1/agents/{agent_id}/versions       - List versions for agent
GET    /api/v1/agents/{agent_id}/versions/{id}  - Get version details
```

### Service Interface

```python
class AgentVersionService:
    async def create_version(agent_id: UUID, request: CreateVersionRequest) -> AgentVersionResponse
    async def get_version(agent_id: UUID, version_id: UUID) -> AgentVersionResponse
    async def list_versions(agent_id: UUID, pagination: PaginationParams) -> PaginatedResponse[AgentVersionResponse]
    async def get_latest_version(agent_id: UUID) -> Optional[AgentVersionResponse]
```

## Inputs

### CreateVersionRequest
- `version_number` (string, optional) - Version identifier (auto-generated if not provided)
- `notes` (string, optional) - Version notes/changelog
- `snapshot_metadata` (dict, optional) - Additional snapshot metadata

## Outputs

### AgentVersionResponse
- `id` (UUID) - Version unique identifier
- `agent_id` (UUID) - Parent agent ID
- `version_number` (string) - Version identifier (e.g., "v1", "1.0.0", "2024-01-15")
- `snapshot` (object) - Complete agent configuration snapshot
- `notes` (string) - Version notes
- `snapshot_metadata` (dict) - Additional metadata
- `created_at` (datetime) - Snapshot creation time
- `is_immutable` (bool) - Always true for committed versions

## Dependencies

### Module Dependencies
- `modules.agent_registry` - To fetch agent data for snapshotting
- `core.database` - Database session management
- `core.events` - Event publishing
- `shared.types` - Common types
- `shared.exceptions` - Exception types

### External Dependencies
- SQLAlchemy - Database ORM
- Pydantic - Validation

## Events Emitted

- `AgentVersionCreated` - When new version snapshot is created

## Events Consumed

- `AgentDeleted` - Could trigger version retention policy (future enhancement)

## Database Entities Owned

### agent_versions table
- `id` (UUID, PK)
- `agent_id` (UUID, FK to agents, NOT NULL)
- `version_number` (VARCHAR(100), NOT NULL)
- `snapshot` (JSONB, NOT NULL) - Full agent configuration
- `notes` (TEXT)
- `snapshot_metadata` (JSONB)
- `created_at` (TIMESTAMP, NOT NULL)

Indexes:
- `idx_agent_versions_agent_id` - For agent lookups
- `idx_agent_versions_created_at` - For chronological ordering
- `uk_agent_versions_agent_version` - Unique constraint on (agent_id, version_number)

## Snapshot Structure

The `snapshot` field contains:
```json
{
  "agent_id": "uuid",
  "name": "Agent Name",
  "description": "...",
  "endpoint_url": "https://...",
  "execution_mode": "http",
  "purpose": "...",
  "risk_profile": {...},
  "metadata": {...},
  "tools": [...],  // Tool IDs at snapshot time
  "captured_at": "2024-01-15T10:00:00Z"
}
```

## Validation Rules

### Version Number
- Optional (auto-generated if not provided)
- If provided: 1-100 characters
- Must be unique per agent
- Suggested formats: "v1", "1.0.0", "2024-01-15", "sprint-42"

### Snapshot
- Automatically captured from current agent state
- Includes all agent configuration fields
- Includes associated tool IDs (resolved at snapshot time)
- Immutable after creation

### Notes
- Optional
- Max 5000 characters
- Used for changelog, deployment notes, etc.

## Immutability

**Critical**: Once a version is created, it CANNOT be modified. This ensures:
- Reliable regression testing
- Historical accuracy
- Audit trail integrity

If changes are needed, create a new version instead.

## Version Number Generation

If not provided, version numbers are auto-generated using sequential format:
- First version: "v1"
- Subsequent versions: "v2", "v3", etc.

## Extension Points

### Custom Version Numbering
Additional versioning schemes can be implemented (semantic versioning, date-based, etc.).

### Snapshot Enrichment
Additional data can be included in snapshots (environment variables, dependencies, etc.).

### Retention Policies
Future enhancement to automatically archive old versions.

## Test Strategy

### Unit Tests
- Version number generation logic
- Snapshot capture logic
- Immutability enforcement

### Integration Tests
- Full version creation flow
- Version retrieval with agent lookup
- Pagination of version history

### Contract Tests
- API request/response schemas
- Service interface contracts
- Event schemas

## Security Considerations

- Versions inherit security context from parent agent
- Snapshots may contain sensitive configuration (encrypted at rest)
- Workspace isolation enforced through agent relationship
- Version deletion not allowed (soft delete only if needed)

## Performance Considerations

- Snapshots stored as JSONB for efficient querying
- Version list queries paginated by default
- Indexes on frequently queried fields
- Consider snapshot size limits (e.g., max 1MB per snapshot)

## Module Isolation

This module:
- MUST NOT modify agent data (read-only access through Agent Registry)
- MUST NOT access tool details directly (stores tool IDs only)
- MUST communicate with other modules through events
- SHOULD remain functional if Agent Registry is temporarily unavailable (cached data)

## Future Enhancements

- Version comparison/diff API
- Automatic versioning on agent updates (via event handler)
- Version tags/labels (production, staging, etc.)
- Version rollback capability
- Version retention policies
