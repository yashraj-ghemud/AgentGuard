# Database Ownership

This document defines which module owns which database tables and the rules for cross-module data access.

## Core Principle

**Each module owns its tables exclusively.** No other module may directly read from or write to another module's tables. Cross-module data access must go through service interfaces or events.

## Module Ownership Map

### Agent Registry Module

**Owns:**
- `agents` table

**Schema:**
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    endpoint_url TEXT NOT NULL,
    execution_mode VARCHAR(50) NOT NULL,
    purpose TEXT,
    status entity_status NOT NULL DEFAULT 'active',
    risk_profile JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    workspace_id UUID,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_agents_name ON agents(name);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_workspace_id ON agents(workspace_id);
CREATE INDEX idx_agents_execution_mode ON agents(execution_mode);
```

**Access Pattern:**
- Other modules can read agent data through `AgentRepository.get_by_id()` or `AgentService`
- Other modules MUST NOT write to agents table
- Other modules MUST NOT directly query agents table

### Agent Versioning Module

**Owns:**
- `agent_versions` table

**Schema:**
```sql
CREATE TABLE agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version_number VARCHAR(100) NOT NULL,
    snapshot JSONB NOT NULL,
    notes TEXT,
    snapshot_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uk_agent_versions_agent_version UNIQUE (agent_id, version_number)
);

CREATE INDEX idx_agent_versions_agent_id ON agent_versions(agent_id);
CREATE INDEX idx_agent_versions_created_at ON agent_versions(created_at);
```

**Foreign Keys:**
- `agent_id` → `agents.id` (CASCADE DELETE)

**Access Pattern:**
- Versions are immutable after creation
- Read access through `AgentVersionRepository` or `AgentVersionService`
- Version snapshots contain denormalized agent data (captured at creation time)

### Tool Registry Module

**Owns:**
- `tools` table

**Schema:**
```sql
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB,
    risk_level VARCHAR(50) NOT NULL,
    is_destructive BOOLEAN NOT NULL DEFAULT FALSE,
    is_reversible BOOLEAN NOT NULL DEFAULT TRUE,
    requires_confirmation BOOLEAN NOT NULL DEFAULT FALSE,
    timeout_seconds INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uk_tools_agent_name UNIQUE (agent_id, name)
);

CREATE INDEX idx_tools_agent_id ON tools(agent_id);
CREATE INDEX idx_tools_risk_level ON tools(risk_level);
CREATE INDEX idx_tools_status ON tools(status);
```

**Foreign Keys:**
- `agent_id` → `agents.id` (CASCADE DELETE)

**Access Pattern:**
- Read through `ToolRepository` or `ToolService`
- Tool schemas stored as JSONB for flexibility
- Risk levels guide execution policies

## Future Module Tables (Part 2+)

### Scenario Engine Module
- `scenarios` table
- `scenario_suites` table

### Execution Engine Module
- `executions` table
- `execution_steps` table

### Trace Engine Module
- `traces` table
- `trace_events` table

### Evaluation Engine Module
- `evaluation_results` table
- `evaluation_metrics` table

### Failure Classification Module
- `failures` table
- `failure_patterns` table

### Scoring Engine Module
- `scores` table
- `score_history` table

### Regression Engine Module
- `regressions` table
- `regression_comparisons` table

### Reporting Engine Module
- `reports` table
- `report_schedules` table

### Scheduling Engine Module
- `scheduled_evaluations` table
- `schedule_runs` table

### Notification System Module
- `notifications` table
- `notification_preferences` table

### Workspace Management Module
- `workspaces` table
- `workspace_members` table
- `workspace_permissions` table

## Cross-Module Access Rules

### ✅ ALLOWED

1. **Read through service interface:**
   ```python
   # Tool Registry needs agent info
   agent = agent_repository.get_by_id(agent_id)
   if not agent:
       raise NotFoundError("Agent", str(agent_id))
   ```

2. **Subscribe to domain events:**
   ```python
   # Versioning listens to AgentDeleted event
   event_publisher.subscribe("agent.deleted", handle_agent_deleted)
   ```

3. **Foreign key relationships:**
   ```python
   # agent_versions.agent_id → agents.id (defined in migration)
   ```

4. **Denormalized snapshots:**
   ```python
   # Version snapshot includes agent data (captured at version creation)
   snapshot = {
       "agent_id": agent.id,
       "name": agent.name,
       # ... complete agent state
   }
   ```

### ❌ FORBIDDEN

1. **Direct table access across modules:**
   ```python
   # WRONG: Tool Registry directly querying agents table
   stmt = select(Agent).where(Agent.id == agent_id)
   ```

2. **Cross-module writes:**
   ```python
   # WRONG: Versioning module updating agents table
   agent.name = "Modified by Versioning"
   ```

3. **Bypassing service layer:**
   ```python
   # WRONG: Using SQLAlchemy session directly
   db.query(Agent).filter_by(id=agent_id).first()
   ```

4. **Tight coupling through imports:**
   ```python
   # WRONG: Importing implementation details
   from modules.agent_registry.infrastructure.repository import AgentRepository
   # CORRECT: Use dependency injection
   def __init__(self, agent_repository: AgentRepository):
   ```

## Data Consistency

### Transactional Boundaries

Each module maintains its own transactional boundary:
- Agent creation is atomic within Agent Registry
- Version creation is atomic within Agent Versioning
- Tool registration is atomic within Tool Registry

Cross-module operations use eventual consistency through events.

### Referential Integrity

Foreign keys enforce referential integrity:
- Deleting an agent cascades to versions and tools
- Database ensures no orphaned records
- Application handles cleanup through events

### Eventual Consistency

When modules need coordinated state:
1. Primary operation completes
2. Event published
3. Subscribers react asynchronously
4. Each subscriber has its own transaction

Example:
```
1. Agent deleted (Agent Registry commits)
2. AgentDeleted event published
3. Versioning module archives versions (separate transaction)
4. Tool Registry archives tools (separate transaction)
```

## Migration Strategy

### Adding New Tables

1. Create migration in module's context
2. Document ownership in this file
3. Define foreign keys if needed
4. Create indexes for common queries
5. Add constraints (unique, check, etc.)

### Modifying Existing Tables

1. Only the owning module can modify its tables
2. Breaking changes require:
   - Version bump (v2, v3, etc.)
   - Migration path for existing data
   - Backward compatibility period
3. Non-breaking changes (add column) are allowed

### Example Migration

```python
# Migration: Add description column to agents
def upgrade():
    op.add_column('agents', sa.Column('description', sa.Text))

def downgrade():
    op.drop_column('agents', 'description')
```

## Performance Considerations

### Indexing Strategy

Each module indexes its tables based on access patterns:
- Foreign keys are always indexed
- Status columns are indexed
- Timestamp columns for sorting are indexed
- Unique constraints create implicit indexes

### Query Optimization

- Use select_related/joinedload for foreign keys
- Paginate list queries
- Use database-level filtering before loading to application
- JSONB columns use GIN indexes where needed

### Caching

Modules may cache their own data:
- Cache invalidation on write operations
- Cache TTL based on data volatility
- No caching of other module's data

## Backup and Recovery

### Backup Strategy

- Full database backup daily
- Point-in-time recovery enabled
- Per-module restore possible through foreign keys

### Data Retention

- Soft deletes for audit trail (status='archived')
- Hard deletes only after retention period
- Immutable tables (agent_versions) never deleted

## Testing Isolation

### Test Database

Each test suite uses isolated test database:
```python
# Test setup
test_db = create_test_engine()
Base.metadata.create_all(test_db)

# Test teardown
Base.metadata.drop_all(test_db)
```

### Test Data

Use factories for test data:
```python
# Good: Factory creates valid test agent
agent = AgentFactory.create(name="Test Agent")

# Bad: Manual SQL insertion
db.execute("INSERT INTO agents ...")
```

## Monitoring

### Metrics to Track

- Query performance per table
- Foreign key constraint violations
- Transaction rollback rates
- Table growth rates
- Index usage statistics

### Alerts

- Slow queries (>1s)
- Failed foreign key constraints
- Database connection pool exhaustion
- Deadlocks or lock timeouts

## Questions?

For questions about database ownership or access patterns:
1. Check this document first
2. Review module README files
3. Consult the architecture documentation
4. Ask the platform team
