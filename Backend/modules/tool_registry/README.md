# Tool Registry Module

## Purpose

The Tool Registry module manages tool definitions that AI agents can use during execution. Each tool represents an action or capability with defined inputs, outputs, and risk characteristics.

## Responsibilities

- **Tool Registration** - Define and register tools with schemas
- **Tool Management** - CRUD operations for tools
- **Agent-Tool Association** - Link tools to specific agents
- **Risk Assessment** - Classify tools by risk level and characteristics
- **Schema Validation** - Validate tool input/output schemas
- **Tool Metadata** - Store tool documentation and constraints

## Non-Responsibilities

- Tool execution (handled by Execution Engine)
- Runtime validation of tool calls (handled by Execution Engine)
- Tool result evaluation (handled by Evaluation Engine)
- Agent definitions (handled by Agent Registry)
- Permission enforcement (handled by Auth layer)

## Public Interfaces

### REST API

```
POST   /api/v1/agents/{agent_id}/tools      - Register tool for agent
GET    /api/v1/agents/{agent_id}/tools      - List agent's tools
GET    /api/v1/tools/{tool_id}              - Get tool details
PATCH  /api/v1/tools/{tool_id}              - Update tool
DELETE /api/v1/tools/{tool_id}              - Archive tool
```

### Service Interface

```python
class ToolService:
    async def register_tool(agent_id: UUID, request: RegisterToolRequest) -> ToolResponse
    async def get_tool(tool_id: UUID) -> ToolResponse
    async def list_agent_tools(agent_id: UUID, pagination: PaginationParams) -> PaginatedResponse[ToolResponse]
    async def update_tool(tool_id: UUID, request: UpdateToolRequest) -> ToolResponse
    async def archive_tool(tool_id: UUID) -> None
```

## Inputs

### RegisterToolRequest
- `name` (string, required) - Tool name
- `description` (string, required) - Tool description
- `input_schema` (object, required) - JSON schema for inputs
- `output_schema` (object, optional) - JSON schema for outputs
- `risk_level` (enum, required) - low, medium, high, critical
- `is_destructive` (bool, default: false) - Whether tool modifies state
- `is_reversible` (bool, default: true) - Whether action can be undone
- `requires_confirmation` (bool, default: false) - Requires user approval
- `timeout_seconds` (int, optional) - Max execution time
- `metadata` (dict, optional) - Additional metadata

### UpdateToolRequest
- All fields optional, only provided fields are updated

## Outputs

### ToolResponse
- `id` (UUID) - Tool unique identifier
- `agent_id` (UUID) - Associated agent
- `name` (string) - Tool name
- `description` (string) - Tool description
- `input_schema` (object) - Input JSON schema
- `output_schema` (object) - Output JSON schema
- `risk_level` (enum) - Risk classification
- `is_destructive` (bool) - Destructive flag
- `is_reversible` (bool) - Reversibility flag
- `requires_confirmation` (bool) - Confirmation requirement
- `timeout_seconds` (int) - Timeout setting
- `status` (enum) - active, inactive, archived
- `metadata` (dict) - Additional metadata
- `created_at` (datetime) - Creation timestamp
- `updated_at` (datetime) - Last update timestamp

## Dependencies

### Module Dependencies
- `modules.agent_registry` - To verify agent existence
- `core.database` - Database session management
- `core.events` - Event publishing
- `shared.types` - Common types (RiskLevel, etc.)
- `shared.exceptions` - Exception types

### External Dependencies
- SQLAlchemy - Database ORM
- Pydantic - Validation
- jsonschema - JSON schema validation

## Events Emitted

- `ToolRegistered` - When tool is registered
- `ToolUpdated` - When tool is modified
- `ToolDeleted` - When tool is archived

## Events Consumed

- `AgentDeleted` - Could trigger cascade deletion (handled by FK constraint)

## Database Entities Owned

### tools table
- `id` (UUID, PK)
- `agent_id` (UUID, FK to agents, NOT NULL)
- `name` (VARCHAR(255), NOT NULL)
- `description` (TEXT, NOT NULL)
- `input_schema` (JSONB, NOT NULL)
- `output_schema` (JSONB)
- `risk_level` (VARCHAR(50), NOT NULL)
- `is_destructive` (BOOLEAN, DEFAULT false)
- `is_reversible` (BOOLEAN, DEFAULT true)
- `requires_confirmation` (BOOLEAN, DEFAULT false)
- `timeout_seconds` (INTEGER)
- `status` (VARCHAR(50), NOT NULL, DEFAULT 'active')
- `metadata` (JSONB)
- `created_at` (TIMESTAMP, NOT NULL)
- `updated_at` (TIMESTAMP, NOT NULL)

Indexes:
- `idx_tools_agent_id` - For agent lookups
- `idx_tools_risk_level` - For risk-based queries
- `idx_tools_status` - For status filtering
- `uk_tools_agent_name` - Unique constraint on (agent_id, name)

## Validation Rules

### Tool Name
- Required
- 1-255 characters
- Must be unique per agent
- Alphanumeric, underscores, hyphens allowed
- Should follow function naming conventions

### Description
- Required
- 1-5000 characters
- Should clearly explain tool purpose and behavior

### Input Schema
- Required
- Must be valid JSON Schema
- Should define all required parameters
- Should include descriptions for each field

### Output Schema
- Optional
- Must be valid JSON Schema if provided
- Defines expected return structure

### Risk Level
- Required
- Must be one of: low, medium, high, critical
- Determines execution policies and approval requirements

### Timeout
- Optional
- If provided: 1-3600 seconds
- Default enforced at execution time

## Risk Classification Guidelines

### Low Risk
- Read-only operations
- No external side effects
- Safe to retry
- Examples: search, get_info, calculate

### Medium Risk
- Limited side effects
- Reversible actions
- Moderate resource usage
- Examples: send_email, create_draft, cache_data

### High Risk
- Significant side effects
- May be irreversible
- High resource usage
- Examples: publish_content, charge_payment, delete_resource

### Critical Risk
- Irreversible destructive actions
- Major security/financial impact
- Requires explicit approval
- Examples: delete_database, refund_transaction, terminate_service

## Extension Points

### Custom Risk Policies
Additional risk assessment logic can be added per organization.

### Schema Validators
Custom validators for specific schema patterns.

### Tool Categories
Tools can be categorized (data_access, communication, file_operations, etc.).

## Test Strategy

### Unit Tests
- Schema validation logic
- Risk level validation
- Name uniqueness checks

### Integration Tests
- Full tool registration flow
- Agent-tool association
- Tool retrieval with agent context

### Contract Tests
- API request/response schemas
- Service interface contracts
- Event schemas

## Security Considerations

- Tool schemas may reveal system architecture (careful in multi-tenant)
- Risk levels enforced at execution time, not registration
- Destructive tools should always require confirmation
- Timeout limits prevent resource exhaustion
- Workspace isolation through agent relationship

## Performance Considerations

- Tool list queries use pagination
- Indexes on frequently queried fields
- JSONB schemas stored efficiently
- Schema validation only on registration (not retrieval)

## Module Isolation

This module:
- MUST NOT execute tools (execution is separate concern)
- MUST NOT modify agent data directly
- MUST verify agent existence before tool registration
- SHOULD remain functional if Execution Engine is unavailable

## JSON Schema Examples

### Input Schema Example
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 10
    }
  },
  "required": ["query"]
}
```

### Output Schema Example
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {"type": "object"}
    },
    "total": {
      "type": "integer"
    }
  }
}
```
