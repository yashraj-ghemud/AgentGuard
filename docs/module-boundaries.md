# Module Boundaries

This document defines the boundaries, contracts, and communication rules between AgentGuard modules.

## Core Principle

**Modules communicate through stable contracts, not implementation details.**

Each module:
- Owns its database tables exclusively
- Exposes public service interfaces
- Publishes domain events for state changes
- Subscribes to events from other modules
- MUST NOT import implementation details from other modules

## Module Dependency Graph

```
┌──────────────────────────────────────────────────────┐
│                   Core Platform                       │
│  (database, config, events, execution, observability)│
└──────────────────────┬───────────────────────────────┘
                       │ (all modules depend on core)
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼─────────┐         ┌────────▼──────────┐
│  Agent Registry │         │   Tool Registry    │
└───────┬─────────┘         └────────┬──────────┘
        │                            │
        │ (reads agent data)         │ (reads agent data)
        │                            │
        └────────────┬───────────────┘
                     │
              ┌──────▼────────────┐
              │ Agent Versioning  │
              │ (reads agent data)│
              └───────────────────┘
```

**Dependency Rules:**
- Core Platform has NO dependencies on modules
- Modules depend on Core Platform
- Modules MAY read from other modules through service interfaces
- Modules MUST NOT write to other modules' tables
- Modules MAY subscribe to other modules' events

## Module Contracts

### Agent Registry

**Provides:**
```python
class AgentService:
    async def create_agent(request: CreateAgentRequest) -> AgentResponse
    def get_agent(agent_id: UUID) -> AgentResponse
    def list_agents(filters, pagination) -> PaginatedResponse[AgentResponse]
    async def update_agent(agent_id, request) -> AgentResponse
    async def archive_agent(agent_id) -> None

class AgentRepository:
    def get_by_id(agent_id: UUID) -> Optional[Agent]
    def get_by_name(name: str, workspace_id) -> Optional[Agent]
    def exists_by_name(name: str, workspace_id, exclude_id) -> bool
```

**Events:**
- `AgentCreated(agent_id, agent_name, workspace_id)`
- `AgentUpdated(agent_id, agent_name, changes, workspace_id)`
- `AgentDeleted(agent_id, agent_name, workspace_id)`

**Consumes:** None

### Agent Versioning

**Provides:**
```python
class AgentVersionService:
    async def create_version(agent_id, request) -> AgentVersionResponse
    def get_version(agent_id, version_id) -> AgentVersionResponse
    def list_versions(agent_id, pagination) -> PaginatedResponse
    def get_latest_version(agent_id) -> Optional[AgentVersionResponse]
```

**Events:**
- `AgentVersionCreated(agent_id, version_id, version_number, workspace_id)`

**Consumes:**
- `AgentDeleted` - Could trigger version cleanup (future)

**Dependencies:**
- Reads agent data via `AgentRepository.get_by_id()`

### Tool Registry

**Provides:**
```python
class ToolService:
    async def register_tool(agent_id, request) -> ToolResponse
    def get_tool(tool_id) -> ToolResponse
    def list_agent_tools(agent_id, filters, pagination) -> PaginatedResponse
    async def update_tool(tool_id, request) -> ToolResponse
    async def archive_tool(tool_id) -> None
```

**Events:**
- `ToolRegistered(tool_id, tool_name, agent_id, risk_level, workspace_id)`
- `ToolUpdated(tool_id, tool_name, agent_id, changes)`
- `ToolDeleted(tool_id, tool_name, agent_id)`

**Consumes:**
- `AgentDeleted` - Handled by CASCADE DELETE

**Dependencies:**
- Reads agent data via `AgentRepository.get_by_id()`

## Communication Patterns

### Pattern 1: Synchronous Service Call

**When to use:** Need immediate response, blocking operation

**Example:** Tool Registry verifying agent exists

```python
# Tool Registry code
agent = agent_repository.get_by_id(agent_id)
if not agent:
    raise NotFoundError("Agent", str(agent_id))
```

**Rules:**
- Use repository/service interfaces only
- Never query another module's tables directly
- Handle NotFoundError gracefully

### Pattern 2: Asynchronous Event

**When to use:** State change notification, non-blocking

**Example:** Agent Registry notifying of agent creation

```python
# Agent Registry publishes
await event_publisher.publish(
    AgentCreated(
        agent_id=agent.id,
        agent_name=agent.name,
        workspace_id=agent.workspace_id,
    )
)

# Other module subscribes
def handle_agent_created(event: AgentCreated):
    logger.info(f"Agent created: {event.agent_name}")
    # Perform async operations

event_publisher.subscribe("agent.created", handle_agent_created)
```

**Rules:**
- Events are fire-and-forget
- Subscribers must not fail the publisher
- Use events for eventual consistency
- Event handlers run in separate transactions

### Pattern 3: Foreign Key Relationship

**When to use:** Referential integrity, cascade operations

**Example:** Agent versions referencing agents

```python
# In migration
sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE')
```

**Rules:**
- Only for parent-child relationships
- Use CASCADE for cleanup
- Document in database-ownership.md
- Application code should also handle deletion

### Pattern 4: Denormalized Data

**When to use:** Point-in-time snapshot, performance

**Example:** Version snapshot storing agent data

```python
snapshot = {
    "agent_id": agent.id,
    "name": agent.name,
    # Complete agent state at this moment
}
```

**Rules:**
- Used for immutable records
- Accepts data staleness
- Reduces coupling
- No foreign key required

## Boundary Violations (Anti-Patterns)

### ❌ Direct Table Access

```python
# WRONG: Tool Registry querying agents table directly
from modules.agent_registry.domain.models import Agent
stmt = select(Agent).where(Agent.id == agent_id)
agent = db.execute(stmt).scalar_one()
```

**Why wrong:** Tight coupling, bypasses business logic, breaks encapsulation

**Fix:** Use repository/service interface

### ❌ Cross-Module Write

```python
# WRONG: Versioning updating agent
agent = agent_repository.get_by_id(agent_id)
agent.status = "archived"
db.commit()
```

**Why wrong:** Violates ownership, bypasses validation, causes inconsistency

**Fix:** Call AgentService.update_agent() or publish event

### ❌ Implementation Import

```python
# WRONG: Importing internal classes
from modules.agent_registry.infrastructure.repository import AgentRepository

# CORRECT: Use dependency injection
def __init__(self, agent_repository: AgentRepository):
    self.agent_repository = agent_repository
```

**Why wrong:** Tight coupling, hard to test, breaks modularity

**Fix:** Use dependency injection, inject via constructor

### ❌ Synchronous Event Handling

```python
# WRONG: Blocking in event handler
def handle_agent_created(event):
    result = expensive_operation()  # Blocks publisher
    db.commit()  # In publisher's transaction
```

**Why wrong:** Couples transaction, slow, can cause deadlocks

**Fix:** Use async handler, separate transaction

## Module Extension Points

### Adding New Module

1. **Define contract first:**
   - Write README.md with purpose, responsibilities, non-responsibilities
   - Define public interfaces
   - Define events emitted/consumed
   - Define database tables owned

2. **Implement module:**
   - Follow layered architecture
   - Create interface/domain/application/infrastructure
   - Implement service and repository
   - Add API routes

3. **Integrate:**
   - Register routes in main.py
   - Create database migration
   - Document in module-boundaries.md
   - Add to architecture.md

4. **Test:**
   - Unit tests for domain logic
   - Integration tests for API
   - Contract tests for interfaces
   - Verify no boundary violations

### Modifying Existing Module

**Non-Breaking Changes (OK):**
- Add new endpoint
- Add optional field to request
- Add field to response
- Add new event
- Add new method to service

**Breaking Changes (Requires Version Bump):**
- Remove endpoint
- Remove field from response
- Change field type
- Rename field
- Change event schema
- Change method signature

**Process for Breaking Changes:**
1. Create new version (v2)
2. Deprecate old version
3. Provide migration guide
4. Support both for transition period
5. Remove old version after notice period

## Testing Module Boundaries

### Contract Tests

```python
def test_agent_repository_contract():
    """Verify AgentRepository implements expected interface."""
    repo = AgentRepository(db)
    
    # Test get_by_id returns Agent or None
    agent = repo.get_by_id(uuid4())
    assert agent is None or isinstance(agent, Agent)
    
    # Test get_by_name signature
    agent = repo.get_by_name("test", None)
    assert agent is None or isinstance(agent, Agent)
```

### Integration Tests

```python
def test_tool_registry_uses_agent_service():
    """Verify Tool Registry properly uses Agent Registry."""
    # Create agent through Agent Registry
    agent = create_test_agent()
    
    # Register tool through Tool Registry
    tool = register_test_tool(agent.id)
    
    # Verify tool was created
    assert tool.agent_id == agent.id
```

### Boundary Violation Tests

```python
def test_no_cross_module_table_access():
    """Verify modules don't access other modules' tables."""
    # This would be a static analysis check
    # Scan code for direct table imports
    pass
```

## Documentation Requirements

Each module MUST have:

1. **README.md** containing:
   - Purpose
   - Responsibilities
   - Non-responsibilities
   - Public interfaces
   - Inputs/outputs
   - Dependencies
   - Events emitted/consumed
   - Database entities owned
   - Validation rules
   - Extension points
   - Test strategy

2. **API Documentation:**
   - OpenAPI/Swagger docs
   - Request/response examples
   - Error responses
   - Authentication requirements

3. **Database Documentation:**
   - Table schema
   - Indexes
   - Foreign keys
   - Constraints
   - Migration history

## Questions?

- **"Can my module call another module's service?"**
  - Yes, through dependency injection
  - Read-only access
  - Never write to another module's data

- **"Can I listen to another module's events?"**
  - Yes, subscribe to events
  - Handle in your own transaction
  - Don't block the publisher

- **"Can I add a foreign key to another module's table?"**
  - Yes, for parent-child relationships
  - Document in database-ownership.md
  - Use CASCADE DELETE appropriately

- **"Can I modify another module's table?"**
  - No, never
  - Call their service instead
  - Or publish an event they can react to

- **"How do I share code between modules?"**
  - Put truly shared code in `shared/`
  - Avoid dumping utilities there
  - Consider if code belongs to a module instead

## Enforcement

**Manual Review:**
- Code review checklist
- Architecture review for new modules
- Pull request approval process

**Automated:**
- Import analysis (future)
- Database access audit (future)
- Contract tests
- Integration tests

## Evolution

As the system grows:
- Modules may be extracted to microservices
- Event bus may become distributed (Kafka, RabbitMQ)
- Synchronous calls may become async
- Database may be split (one per service)

The module boundaries prepare for this evolution.
