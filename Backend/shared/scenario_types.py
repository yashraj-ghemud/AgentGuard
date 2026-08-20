"""
Shared type definitions for Part 2: Scenario Generation.

These types are used across scenario generation modules.
"""
from enum import Enum


# ============================================================================
# Scenario Categories
# ============================================================================

class ScenarioCategory(str, Enum):
    """Test scenario categories."""
    NORMAL = "normal"
    EDGE_CASE = "edge_case"
    AMBIGUOUS = "ambiguous"
    ADVERSARIAL = "adversarial"
    INSTRUCTION_CONFLICT = "instruction_conflict"
    GOAL_DRIFT = "goal_drift"
    SAFETY_CRITICAL = "safety_critical"
    TOOL_FAILURE = "tool_failure"
    TOOL_MISUSE = "tool_misuse"
    HALLUCINATION_RESISTANCE = "hallucination_resistance"
    RECOVERY = "recovery"
    CONTEXT_RETENTION = "context_retention"
    RESOURCE_LIMIT = "resource_limit"
    PROMPT_INJECTION = "prompt_injection"


# ============================================================================
# Expected Behavior Types
# ============================================================================

class ExpectedBehaviorType(str, Enum):
    """Types of expected agent behaviors."""
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


# ============================================================================
# Difficulty Levels
# ============================================================================

class DifficultyLevel(str, Enum):
    """Scenario difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


# ============================================================================
# Priority Levels
# ============================================================================

class PriorityLevel(str, Enum):
    """Scenario priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Scenario Status
# ============================================================================

class ScenarioStatus(str, Enum):
    """Scenario lifecycle status."""
    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================================
# Suite Types
# ============================================================================

class SuiteType(str, Enum):
    """Scenario suite types."""
    BASELINE = "baseline"
    ADVERSARIAL = "adversarial"
    SAFETY = "safety"
    TOOL_RELIABILITY = "tool_reliability"
    REGRESSION = "regression"
    FULL_RED_TEAM = "full_red_team"
    CUSTOM = "custom"


# ============================================================================
# Suite Status
# ============================================================================

class SuiteStatus(str, Enum):
    """Scenario suite lifecycle status."""
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    LOCKED = "locked"  # Locked for execution


# ============================================================================
# Generation Run Status
# ============================================================================

class GenerationRunStatus(str, Enum):
    """Status of a scenario generation run."""
    QUEUED = "queued"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    VALIDATING = "validating"
    DEDUPLICATING = "deduplicating"
    PRIORITIZING = "prioritizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Overall Risk Assessment
# ============================================================================

class OverallRisk(str, Enum):
    """Overall risk assessment for an agent."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Test Intensity
# ============================================================================

class TestIntensity(str, Enum):
    """Recommended test intensity based on risk."""
    LIGHT = "light"
    MODERATE = "moderate"
    THOROUGH = "thorough"
    EXHAUSTIVE = "exhaustive"
