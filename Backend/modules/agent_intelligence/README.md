# Agent Intelligence Engine (Module 04)

## Purpose

Converts raw agent metadata into structured intelligence about the agent's capabilities, risks, and potential failure points using LLM-powered analysis.

## Architecture

```
Interface Layer (routes.py)
    ↓
Application Layer (service.py)
    ↓
Domain Layer (models.py, schemas.py)
    ↓
Infrastructure Layer (repository.py)
```

## Key Components

### Domain Models

**AgentCapabilityProfile**: Database model storing structured intelligence
- Primary/secondary goals
- Capabilities and domains
- Tool capabilities with risk assessment
- High-risk, destructive, and reversible operations
- Required and optional inputs
- Ambiguity points (where users might be unclear)
- Failure surfaces (where agent might fail)
- Security surfaces (vulnerability points)
- Assumptions and constraints
- Confidence scores per dimension

### Schemas

**AgentCapabilityAnalysis**: Pydantic schema for LLM structured output
- Enforces strict validation on LLM responses
- Nested structures for capabilities, operations, etc.
- Confidence scoring for quality assessment

**API Schemas**:
- `AnalyzeAgentRequest`: Request to analyze agent
- `AgentCapabilityProfileResponse`: API response format

### Service

**AgentIntelligenceService**: Core business logic
- `analyze_agent()`: Generate capability profile using LLM
- Builds context-rich prompts from agent + tool data
- Validates LLM output against Pydantic schema
- Caches results to avoid redundant analysis
- Publishes domain events

### Repository

**AgentIntelligenceRepository**: Data access
- CRUD operations for capability profiles
- Query by agent ID or version ID
- History tracking

## API Endpoints

### POST /api/v1/agents/{agent_id}/intelligence/analyze

Analyze agent to generate capability profile.

**Query Parameters**:
- `version_id` (optional): Specific version to analyze
- `force_regenerate` (optional): Force new analysis even if cached

**Response**: `AgentCapabilityProfileResponse`

### GET /api/v1/agents/{agent_id}/intelligence

Get existing capability profile (most recent).

**Query Parameters**:
- `version_id` (optional): Get profile for specific version

**Response**: `AgentCapabilityProfileResponse`

### GET /api/v1/agents/{agent_id}/intelligence/history

Get analysis history for an agent.

**Query Parameters**:
- `limit` (default: 10): Maximum results

**Response**: `List[AgentCapabilityProfileResponse]`

## LLM Analysis Process

1. **Data Collection**:
   - Agent metadata (name, description, execution mode)
   - Registered tools with risk levels
   - Risk profile configuration
   - Custom constraints (if provided)

2. **Prompt Construction**:
   - System prompt: Defines analyzer role and focus areas
   - User prompt: Structured agent information + tools
   - Clear instructions for analysis dimensions

3. **LLM Generation**:
   - Model: Configurable (default: gpt-4-turbo-preview)
   - Temperature: 0.3 (focused analysis)
   - Output: Strictly validated against `AgentCapabilityAnalysis` schema

4. **Validation**:
   - Pydantic validates structure
   - Rejects invalid/incomplete responses
   - Retries on validation failure (up to max retries)

5. **Storage**:
   - Convert to database model
   - Store with generation metadata
   - Cache for future requests

## Domain Events

- `AgentAnalysisStarted`: Analysis initiated
- `AgentAnalysisCompleted`: Analysis successful
- `AgentAnalysisFailed`: Analysis failed

## Example Usage

### Analyze Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/intelligence/analyze"
```

### Get Existing Profile

```bash
curl "http://localhost:8000/api/v1/agents/{agent_id}/intelligence"
```

### Force Regeneration

```bash
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/intelligence/analyze?force_regenerate=true"
```

## Configuration

Environment variables (in `.env`):

```env
# Model for agent analysis
AGENT_ANALYSIS_MODEL=gpt-4-turbo-preview
AGENT_ANALYSIS_TEMPERATURE=0.3

# OpenAI API key
OPENAI_API_KEY=your-key-here
```

## Testing

Mock LLM provider available for testing without API calls:

```python
from core.llm import create_mock_provider, set_llm_provider
from modules.agent_intelligence.domain.schemas import AgentCapabilityAnalysis

# Setup
mock = create_mock_provider()
mock.set_default_structured_response(
    AgentCapabilityAnalysis,
    {
        "primary_goal": "Test goal",
        "capabilities": [],
        # ... rest of required fields
    }
)
set_llm_provider(mock)

# Test
profile = await service.analyze_agent(agent_id)
```

## Integration with Other Modules

**Consumes**:
- Agent Registry: Agent metadata
- Tool Registry: Tool definitions and risk levels

**Produces**:
- Capability profiles for Risk Analysis Engine
- Intelligence for Test Strategy Planner
- Context for Scenario Generator

**Events Published**:
- Analysis lifecycle events
- Consumed by observability and monitoring

## Quality Metrics

Capability profiles include confidence scores:
- `goal_understanding`: How well agent's purpose is understood
- `capability_completeness`: Coverage of agent capabilities
- `risk_assessment`: Confidence in risk identification
- `failure_coverage`: Coverage of failure scenarios
- `overall`: Overall analysis quality

Low confidence scores may trigger:
- Warnings to users
- Automatic re-analysis with more context
- Manual review flags

## Future Enhancements

- Multi-model consensus (run analysis with multiple LLMs, compare)
- Human feedback loop (allow manual corrections)
- Continuous learning (improve prompts based on outcomes)
- Capability drift detection (alert when agent changes significantly)
- Domain-specific analysis templates (customize for different agent types)
