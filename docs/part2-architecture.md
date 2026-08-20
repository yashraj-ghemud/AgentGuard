# Part 2 Architecture: Scenario Generation Engine

## Overview

Part 2 transforms raw agent metadata into intelligent, executable test scenarios through AI-powered analysis and generation.

**Goal**: Produce high-quality, structured, versioned test scenarios that Part 3 will execute.

**NOT in scope**: Agent execution, sandbox orchestration, evaluation (those are Part 3+).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Part 1 (Existing)                        │
│  Agent Registry │ Agent Versioning │ Tool Registry │ Core Platform│
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Part 2: Scenario Generation                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 04: Agent Intelligence Engine                    │   │
│  │  - Converts agent metadata → AgentCapabilityProfile      │   │
│  │  - Uses LLM to understand goals, capabilities, risks     │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│                       ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 05: Risk Analysis Engine                         │   │
│  │  - Analyzes tools and operations → RiskProfile           │   │
│  │  - Identifies high-risk operations, inconsistencies      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│                       ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 06: Test Strategy Planner                        │   │
│  │  - Creates TestStrategy with category distribution       │   │
│  │  - Determines scenario counts, priorities, coverage      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│                       ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 07: Scenario Generation Engine                   │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ Step 1: Scenario Seed Generation                 │    │   │
│  │  └──────────────────┬──────────────────────────────┘    │   │
│  │  ┌──────────────────↓──────────────────────────────┐    │   │
│  │  │ Step 2: Scenario Expansion                       │    │   │
│  │  └──────────────────┬──────────────────────────────┘    │   │
│  │  ┌──────────────────↓──────────────────────────────┐    │   │
│  │  │ Step 3: Adversarial Mutation                     │    │   │
│  │  └──────────────────┬──────────────────────────────┘    │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│                       ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 08: Scenario Validation Engine                   │   │
│  │  - Validates relevance, executability, quality           │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│                       ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 09: Scenario Deduplication Engine                │   │
│  │  - Semantic similarity, intent matching                   │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│                       ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 10: Scenario Prioritization Engine               │   │
│  │  - Ranks by risk, coverage, difficulty                   │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       │                                           │
│                       ↓                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Module 11: Scenario Suite Manager                       │   │
│  │  - Creates immutable, versioned test suites              │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                                                                   │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         ↓
                  ┌──────────────┐
                  │ ScenarioSuite │
                  │  (Immutable)  │
                  └──────┬────────┘
                         │
                         ↓
              ┌──────────────────────┐
              │   Part 3: Execution   │
              │   (Future)            │
              └──────────────────────┘
```

## Module Boundaries

### Module 04: Agent Intelligence Engine

**Responsibility**: Convert agent metadata into structured intelligence.

**Input**:
- Agent ID (from Agent Registry)
- Agent Version ID (from Agent Versioning)
- Tool definitions (from Tool Registry)
- Optional: developer-provided constraints

**Output**:
- `AgentCapabilityProfile` (structured, validated)

**Dependencies**:
- LLM Provider (abstraction)
- Agent Registry (read-only via service interface)
- Tool Registry (read-only via service interface)

**Storage**:
- `agent_capability_profiles` table

### Module 05: Risk Analysis Engine

**Responsibility**: Analyze tools and operations to identify risks.

**Input**:
- Agent ID
- Tool definitions
- Agent capability profile

**Output**:
- `RiskProfile` (structured)

**Dependencies**:
- LLM Provider (optional for risk reasoning)
- Tool Registry (read-only)
- Agent Intelligence results

**Storage**:
- `risk_profiles` table

### Module 06: Test Strategy Planner

**Responsibility**: Create structured test strategy.

**Input**:
- Agent capability profile
- Risk profile
- Optional: strategy preferences

**Output**:
- `TestStrategy` (with category distribution)

**Dependencies**:
- Agent Intelligence results
- Risk Analysis results
- LLM Provider (for strategy optimization)

**Storage**:
- `test_strategies` table

### Module 07: Scenario Generation Engine

**Responsibility**: Generate relevant test scenarios.

**Input**:
- Test strategy
- Agent capability profile
- Risk profile

**Output**:
- List of `Scenario` objects

**Dependencies**:
- LLM Provider (core dependency)
- All previous modules (read-only)

**Storage**:
- `scenarios` table
- `scenario_generation_runs` table

### Module 08: Scenario Validation Engine

**Responsibility**: Validate scenario quality and consistency.

**Input**:
- Generated scenario

**Output**:
- Validation result (pass/fail + issues)

**Dependencies**:
- LLM Provider (optional for semantic validation)

**Storage**:
- `scenario_quality_scores` table

### Module 09: Scenario Deduplication Engine

**Responsibility**: Detect and remove duplicates.

**Input**:
- List of scenarios

**Output**:
- Deduplicated scenario list

**Dependencies**:
- LLM Provider (for semantic similarity)

**Storage**:
- Updates `scenarios` table (marks duplicates)

### Module 10: Scenario Prioritization Engine

**Responsibility**: Rank scenarios by importance.

**Input**:
- List of validated, deduplicated scenarios

**Output**:
- Prioritized scenario list

**Dependencies**:
- Risk profiles
- Coverage analysis

**Storage**:
- Updates `scenarios` table (priority field)

### Module 11: Scenario Suite Manager

**Responsibility**: Create and manage scenario suites.

**Input**:
- Prioritized scenarios
- Suite configuration

**Output**:
- `ScenarioSuite` (immutable)

**Dependencies**:
- All scenario modules

**Storage**:
- `scenario_suites` table
- `scenario_suite_items` table (many-to-many)

## Database Schema

### agent_capability_profiles

```sql
CREATE TABLE agent_capability_profiles (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version_id UUID REFERENCES agent_versions(id) ON DELETE SET NULL,
    
    -- Structured capability data (JSONB)
    primary_goal TEXT,
    secondary_goals JSONB, -- array of strings
    capabilities JSONB, -- array of capability objects
    domains JSONB, -- array of domain strings
    tool_capabilities JSONB, -- array of tool capability objects
    high_risk_operations JSONB,
    destructive_operations JSONB,
    reversible_operations JSONB,
    required_inputs JSONB,
    optional_inputs JSONB,
    ambiguity_points JSONB,
    failure_surfaces JSONB,
    security_surfaces JSONB,
    assumptions JSONB,
    constraints JSONB,
    
    -- Metadata
    confidence JSONB, -- confidence scores per dimension
    model_used TEXT NOT NULL,
    generator_version TEXT NOT NULL,
    generation_timestamp TIMESTAMPTZ NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(agent_id, version_id)
);

CREATE INDEX idx_capability_agent ON agent_capability_profiles(agent_id);
CREATE INDEX idx_capability_version ON agent_capability_profiles(version_id);
```

### risk_profiles

```sql
CREATE TABLE risk_profiles (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    capability_profile_id UUID REFERENCES agent_capability_profiles(id) ON DELETE CASCADE,
    
    -- Risk assessment
    overall_risk TEXT NOT NULL, -- low, medium, high, critical
    high_risk_tools JSONB, -- array of tool objects
    critical_tools JSONB,
    unsafe_operations JSONB,
    confirmation_required_operations JSONB,
    risk_inconsistencies JSONB, -- detected mismatches
    
    -- Test intensity recommendation
    recommended_test_intensity TEXT NOT NULL,
    recommended_scenario_count INTEGER NOT NULL,
    
    -- Metadata
    model_used TEXT,
    generator_version TEXT NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(agent_id, capability_profile_id)
);

CREATE INDEX idx_risk_agent ON risk_profiles(agent_id);
CREATE INDEX idx_risk_capability ON risk_profiles(capability_profile_id);
```

### test_strategies

```sql
CREATE TABLE test_strategies (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    capability_profile_id UUID REFERENCES agent_capability_profiles(id) ON DELETE CASCADE,
    risk_profile_id UUID REFERENCES risk_profiles(id) ON DELETE CASCADE,
    
    -- Strategy configuration
    name TEXT NOT NULL,
    description TEXT,
    category_distribution JSONB NOT NULL, -- {normal: 20%, edge: 15%, ...}
    total_scenario_count INTEGER NOT NULL,
    multi_turn_percentage INTEGER NOT NULL,
    
    -- Coverage targets
    tool_coverage_targets JSONB, -- per-tool scenario counts
    risk_coverage_targets JSONB,
    
    -- Metadata
    model_used TEXT,
    generator_version TEXT NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_strategy_agent ON test_strategies(agent_id);
```

### scenarios

```sql
CREATE TABLE scenarios (
    id UUID PRIMARY KEY,
    scenario_suite_id UUID REFERENCES scenario_suites(id) ON DELETE CASCADE,
    agent_version_id UUID NOT NULL REFERENCES agent_versions(id) ON DELETE CASCADE,
    
    -- Classification
    category TEXT NOT NULL, -- NORMAL, EDGE_CASE, ADVERSARIAL, etc.
    subtype TEXT,
    
    -- Content
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    difficulty TEXT NOT NULL, -- easy, medium, hard
    priority TEXT NOT NULL, -- low, medium, high, critical
    risk_level TEXT NOT NULL,
    
    -- Scenario data
    user_input TEXT NOT NULL,
    conversation_steps JSONB, -- array of turn objects
    preconditions JSONB,
    environment_requirements JSONB,
    
    -- Expected behavior (structured)
    expected_behavior JSONB NOT NULL, -- array of expectation objects
    validation_rules JSONB NOT NULL, -- array of validation rule objects
    
    -- Targeting
    target_tools JSONB, -- array of tool names
    tags JSONB, -- array of tag strings
    
    -- Quality metadata
    quality_score FLOAT,
    relevance_score FLOAT,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of_id UUID REFERENCES scenarios(id),
    
    -- Generation metadata
    generated_by TEXT NOT NULL, -- generator name
    generator_version TEXT NOT NULL,
    generation_run_id UUID,
    model_used TEXT NOT NULL,
    
    -- Status
    status TEXT NOT NULL DEFAULT 'draft', -- draft, validated, approved, rejected
    rejection_reason TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scenario_suite ON scenarios(scenario_suite_id);
CREATE INDEX idx_scenario_agent_version ON scenarios(agent_version_id);
CREATE INDEX idx_scenario_category ON scenarios(category);
CREATE INDEX idx_scenario_priority ON scenarios(priority);
CREATE INDEX idx_scenario_risk_level ON scenarios(risk_level);
CREATE INDEX idx_scenario_status ON scenarios(status);
CREATE INDEX idx_scenario_generation_run ON scenarios(generation_run_id);
```

### scenario_suites

```sql
CREATE TABLE scenario_suites (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    agent_version_id UUID NOT NULL REFERENCES agent_versions(id) ON DELETE CASCADE,
    test_strategy_id UUID REFERENCES test_strategies(id) ON DELETE SET NULL,
    
    -- Suite metadata
    name TEXT NOT NULL,
    description TEXT,
    suite_type TEXT NOT NULL, -- baseline, adversarial, safety, regression, full
    
    -- Statistics
    total_scenarios INTEGER NOT NULL DEFAULT 0,
    category_counts JSONB, -- {normal: 10, edge: 5, ...}
    priority_counts JSONB,
    risk_counts JSONB,
    
    -- Coverage
    tool_coverage JSONB, -- per-tool coverage percentage
    coverage_score FLOAT,
    
    -- Status
    status TEXT NOT NULL DEFAULT 'draft', -- draft, generating, completed, failed
    generation_started_at TIMESTAMPTZ,
    generation_completed_at TIMESTAMPTZ,
    generation_error TEXT,
    
    -- Immutability
    is_locked BOOLEAN DEFAULT FALSE, -- locked after execution starts
    locked_at TIMESTAMPTZ,
    
    -- Metadata
    generator_version TEXT NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_suite_agent ON scenario_suites(agent_id);
CREATE INDEX idx_suite_agent_version ON scenario_suites(agent_version_id);
CREATE INDEX idx_suite_status ON scenario_suites(status);
CREATE INDEX idx_suite_type ON scenario_suites(suite_type);
```

### scenario_generation_runs

```sql
CREATE TABLE scenario_generation_runs (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    scenario_suite_id UUID REFERENCES scenario_suites(id) ON DELETE CASCADE,
    
    -- Configuration
    requested_count INTEGER NOT NULL,
    strategy_config JSONB NOT NULL,
    
    -- Progress
    status TEXT NOT NULL DEFAULT 'queued', -- queued, analyzing, generating, validating, deduplicating, prioritizing, completed, failed, cancelled
    current_phase TEXT,
    scenarios_generated INTEGER DEFAULT 0,
    scenarios_validated INTEGER DEFAULT 0,
    scenarios_rejected INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds FLOAT,
    
    -- Results
    error_message TEXT,
    error_details JSONB,
    
    -- Resource tracking
    total_llm_calls INTEGER DEFAULT 0,
    estimated_cost FLOAT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gen_run_agent ON scenario_generation_runs(agent_id);
CREATE INDEX idx_gen_run_suite ON scenario_generation_runs(scenario_suite_id);
CREATE INDEX idx_gen_run_status ON scenario_generation_runs(status);
```

## API Contracts

### Agent Intelligence

```
POST /api/v1/agents/{agent_id}/intelligence/analyze
- Request: { version_id?: UUID, force_regenerate?: bool }
- Response: AgentCapabilityProfile
- Status: 202 (async) or 200 (cached)

GET /api/v1/agents/{agent_id}/intelligence
- Response: AgentCapabilityProfile (latest)

GET /api/v1/agents/{agent_id}/intelligence/versions/{version_id}
- Response: AgentCapabilityProfile
```

### Risk Analysis

```
POST /api/v1/agents/{agent_id}/risk/analyze
- Request: { capability_profile_id?: UUID }
- Response: RiskProfile

GET /api/v1/agents/{agent_id}/risk
- Response: RiskProfile (latest)
```

### Test Strategy

```
POST /api/v1/agents/{agent_id}/strategies
- Request: { category_distribution?: object, total_count?: int }
- Response: TestStrategy

GET /api/v1/agents/{agent_id}/strategies
- Response: List[TestStrategy]

GET /api/v1/strategies/{strategy_id}
- Response: TestStrategy
```

### Scenario Generation

```
POST /api/v1/agents/{agent_id}/scenario-suites
- Request: { name, suite_type, strategy_config, scenario_count }
- Response: { suite_id, generation_run_id, status }

GET /api/v1/agents/{agent_id}/scenario-suites
- Query: ?status=, ?suite_type=
- Response: List[ScenarioSuite]

GET /api/v1/scenario-suites/{suite_id}
- Response: ScenarioSuite (with statistics)

GET /api/v1/scenario-suites/{suite_id}/scenarios
- Query: ?category=, ?priority=, ?risk_level=, ?page=, ?page_size=
- Response: PaginatedResponse[Scenario]

GET /api/v1/scenarios/{scenario_id}
- Response: Scenario (full details)

GET /api/v1/scenario-suites/{suite_id}/coverage
- Response: { tool_coverage, category_coverage, risk_coverage }

POST /api/v1/scenario-suites/{suite_id}/regenerate
- Request: { category?, count? }
- Response: { generation_run_id }

GET /api/v1/generation-runs/{run_id}
- Response: ScenarioGenerationRun (with progress)
```

## Event Definitions

```python
# Agent Intelligence Events
class AgentAnalysisStarted(DomainEvent):
    event_type = "agent_intelligence.analysis_started"
    agent_id: UUID
    version_id: Optional[UUID]

class AgentAnalysisCompleted(DomainEvent):
    event_type = "agent_intelligence.analysis_completed"
    agent_id: UUID
    capability_profile_id: UUID
    
class AgentAnalysisFailed(DomainEvent):
    event_type = "agent_intelligence.analysis_failed"
    agent_id: UUID
    error_message: str

# Risk Analysis Events
class RiskAnalysisCompleted(DomainEvent):
    event_type = "risk_analysis.completed"
    agent_id: UUID
    risk_profile_id: UUID
    overall_risk: str

class RiskInconsistencyDetected(DomainEvent):
    event_type = "risk_analysis.inconsistency_detected"
    agent_id: UUID
    tool_id: UUID
    inconsistency_type: str

# Test Strategy Events
class TestStrategyCreated(DomainEvent):
    event_type = "test_strategy.created"
    strategy_id: UUID
    agent_id: UUID

# Scenario Generation Events
class ScenarioGenerationStarted(DomainEvent):
    event_type = "scenario_generation.started"
    generation_run_id: UUID
    agent_id: UUID

class ScenarioGenerated(DomainEvent):
    event_type = "scenario_generation.scenario_generated"
    scenario_id: UUID
    generation_run_id: UUID
    category: str

class ScenarioRejected(DomainEvent):
    event_type = "scenario_generation.scenario_rejected"
    generation_run_id: UUID
    reason: str

class ScenarioGenerationCompleted(DomainEvent):
    event_type = "scenario_generation.completed"
    generation_run_id: UUID
    scenario_suite_id: UUID
    total_scenarios: int

class ScenarioSuiteCreated(DomainEvent):
    event_type = "scenario_suite.created"
    suite_id: UUID
    agent_id: UUID
    suite_type: str
```

## Scenario Taxonomy

```python
class ScenarioCategory(str, Enum):
    NORMAL = "normal"                    # Expected behavior
    EDGE_CASE = "edge_case"              # Unusual but valid
    AMBIGUOUS = "ambiguous"              # Needs clarification
    ADVERSARIAL = "adversarial"          # Manipulation attempts
    INSTRUCTION_CONFLICT = "instruction_conflict"  # Conflicting instructions
    GOAL_DRIFT = "goal_drift"            # Loss of original objective
    SAFETY_CRITICAL = "safety_critical"  # Dangerous operations
    TOOL_FAILURE = "tool_failure"        # Tool errors
    TOOL_MISUSE = "tool_misuse"          # Wrong tool usage
    HALLUCINATION_RESISTANCE = "hallucination_resistance"  # Invented info
    RECOVERY = "recovery"                # Error recovery
    CONTEXT_RETENTION = "context_retention"  # Multi-turn consistency
    RESOURCE_LIMIT = "resource_limit"    # Constrained conditions
    PROMPT_INJECTION = "prompt_injection"  # Injection attacks
```

## Expected Behavior Types

```python
class ExpectedBehaviorType(str, Enum):
    MUST_RESPOND = "must_respond"
    MUST_REFUSE = "must_refuse"
    MUST_CLARIFY = "must_clarify"
    MUST_CONFIRM = "must_confirm"
    MUST_USE_TOOL = "must_use_tool"
    MUST_NOT_USE_TOOL = "must_not_use_tool"
    MUST_RETRY = "must_retry"
    MUST_ABORT = "must_abort"
    MUST_FALLBACK = "must_fallback"
    MUST_REPORT_FAILURE = "must_report_failure"
    MUST_PRESERVE_GOAL = "must_preserve_goal"
```

## LLM Provider Interface

```python
class ILLMProvider(ABC):
    """Interface for LLM providers."""
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> BaseModel:
        """Generate structured output conforming to schema."""
        pass
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate unstructured text."""
        pass
```

## Configuration

```python
# Model policies for different operations
AGENT_ANALYSIS_MODEL = "gpt-4-turbo-preview"
SCENARIO_GENERATION_MODEL = "gpt-4-turbo-preview"
SCENARIO_REVIEW_MODEL = "gpt-3.5-turbo"
MUTATION_MODEL = "gpt-3.5-turbo"

# Generation limits
MAX_SCENARIOS_PER_REQUEST = 100
MAX_GENERATION_TIMEOUT_SECONDS = 3600
MAX_LLM_RETRIES = 3

# Quality thresholds
MIN_SCENARIO_QUALITY_SCORE = 0.6
MIN_RELEVANCE_SCORE = 0.7
```

## Part 3 Integration Contract

Part 3 (Execution Engine) will consume:

```python
@dataclass
class ExecutableScenario:
    """Contract for Part 3 execution."""
    scenario_id: UUID
    agent_version_id: UUID
    category: ScenarioCategory
    user_input: str
    conversation_steps: List[ConversationTurn]
    preconditions: Dict[str, Any]
    expected_behavior: List[ExpectedBehavior]
    validation_rules: List[ValidationRule]
    target_tools: List[str]
    risk_level: RiskLevel
    priority: str
    timeout_seconds: int
```

Part 3 must NOT:
- Know how scenarios were generated
- Modify scenario content
- Depend on generation metadata

Part 3 should:
- Execute scenarios against target agents
- Capture execution traces
- Evaluate against expected behaviors
- Report pass/fail results

## Security Considerations

1. **LLM Output Validation**: All LLM outputs validated against strict Pydantic schemas
2. **Prompt Injection Protection**: System prompts protected, user inputs sanitized
3. **Cost Controls**: Max token limits, request quotas, budget tracking
4. **Rate Limiting**: Per-agent generation limits, cooldown periods
5. **Idempotency**: Generation runs use idempotency keys
6. **Secrets Management**: API keys never logged, stored in environment only

## Scalability Considerations

1. **Async Generation**: Long-running LLM calls don't block API
2. **Job Queue**: Redis-backed queue for generation runs
3. **Parallelization**: Multiple scenarios generated concurrently
4. **Caching**: Capability profiles cached, reused across generations
5. **Pagination**: All list endpoints support pagination
6. **Database Indexes**: Proper indexes on query columns

## Testing Strategy

1. **Unit Tests**: Each module independently testable
2. **Integration Tests**: Module interactions verified
3. **Contract Tests**: API contracts validated
4. **LLM Mocking**: Mock LLM responses for deterministic tests
5. **Quality Tests**: Scenario quality metrics validated
6. **Regression Tests**: Part 1 functionality preserved

## Success Criteria

Part 2 complete when:

- ✅ All 11 modules implemented
- ✅ Database migrations successful
- ✅ API endpoints functional
- ✅ LLM provider abstraction working
- ✅ Scenarios generated successfully
- ✅ Validation, deduplication, prioritization working
- ✅ Scenario suites created
- ✅ Frontend displays generated scenarios
- ✅ Part 1 regression tests pass
- ✅ Documentation complete
- ✅ Part 3 contract documented
