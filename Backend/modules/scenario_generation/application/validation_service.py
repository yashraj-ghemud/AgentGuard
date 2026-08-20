"""
Scenario Validation Service

Validates generated scenarios for quality, completeness, and correctness.
"""
from typing import List, Dict, Any, Tuple
from uuid import UUID

from modules.scenario_generation.domain.schemas import GeneratedScenario
from modules.scenario_generation.domain.models import Scenario
from shared.scenario_types import (
    ScenarioCategory,
    ExpectedBehaviorType,
    DifficultyLevel,
    PriorityLevel,
)


class ValidationResult:
    """Result of scenario validation."""
    
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str], score: float):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.score = score  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "score": self.score
        }


class ScenarioValidationService:
    """
    Service for validating scenario quality.
    
    Validates:
    - Required fields presence
    - Expected behavior completeness
    - Validation rules correctness
    - Multi-turn conversation structure
    - Quality score reasonableness
    - Category/difficulty/priority consistency
    """

    def __init__(self):
        self.min_quality_score = 0.3  # Reject scenarios below this threshold
        self.min_title_length = 10
        self.max_title_length = 200
        self.min_description_length = 20
        self.min_user_input_length = 5
    
    # ========================================================================
    # Main Validation API
    # ========================================================================

    def validate_scenario(
        self,
        scenario: GeneratedScenario,
        strict: bool = True
    ) -> ValidationResult:
        """
        Validate a generated scenario.
        
        Args:
            scenario: The scenario to validate
            strict: If True, warnings become errors
        
        Returns:
            ValidationResult with errors, warnings, and quality score
        """
        errors = []
        warnings = []
        
        # 1. Required fields
        field_errors = self._validate_required_fields(scenario)
        errors.extend(field_errors)
        
        # 2. Field lengths and formats
        format_errors, format_warnings = self._validate_field_formats(scenario)
        errors.extend(format_errors)
        warnings.extend(format_warnings)
        
        # 3. Expected behaviors
        behavior_errors, behavior_warnings = self._validate_expected_behaviors(scenario)
        errors.extend(behavior_errors)
        warnings.extend(behavior_warnings)
        
        # 4. Validation rules
        rule_errors = self._validate_validation_rules(scenario)
        errors.extend(rule_errors)
        
        # 5. Conversation steps
        conv_errors, conv_warnings = self._validate_conversation_steps(scenario)
        errors.extend(conv_errors)
        warnings.extend(conv_warnings)
        
        # 6. Quality score
        quality_errors, quality_warnings = self._validate_quality_score(scenario)
        errors.extend(quality_errors)
        warnings.extend(quality_warnings)
        
        # 7. Category consistency
        consistency_warnings = self._validate_category_consistency(scenario)
        warnings.extend(consistency_warnings)
        
        # If strict, promote warnings to errors
        if strict and warnings:
            errors.extend(warnings)
            warnings = []
        
        # Calculate validation score (0.0 to 1.0)
        validation_score = self._calculate_validation_score(
            errors=errors,
            warnings=warnings,
            quality_score=scenario.quality_score
        )
        
        is_valid = len(errors) == 0 and validation_score >= self.min_quality_score
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            score=validation_score
        )
    
    def validate_batch(
        self,
        scenarios: List[GeneratedScenario],
        strict: bool = True
    ) -> Tuple[List[GeneratedScenario], List[Tuple[GeneratedScenario, ValidationResult]]]:
        """
        Validate a batch of scenarios.
        
        Returns:
            (valid_scenarios, rejected_scenarios_with_reasons)
        """
        valid = []
        rejected = []
        
        for scenario in scenarios:
            result = self.validate_scenario(scenario, strict=strict)
            if result.is_valid:
                valid.append(scenario)
            else:
                rejected.append((scenario, result))
        
        return valid, rejected
    
    # ========================================================================
    # Validation Rules
    # ========================================================================

    def _validate_required_fields(self, scenario: GeneratedScenario) -> List[str]:
        """Validate that required fields are present and non-empty."""
        errors = []
        
        if not scenario.title or not scenario.title.strip():
            errors.append("Missing required field: title")
        
        if not scenario.description or not scenario.description.strip():
            errors.append("Missing required field: description")
        
        if not scenario.user_input or not scenario.user_input.strip():
            errors.append("Missing required field: user_input")
        
        if not scenario.expected_behavior:
            errors.append("Missing required field: expected_behavior (must have at least one)")
        
        if not scenario.validation_rules:
            errors.append("Missing required field: validation_rules (must have at least one)")
        
        if scenario.difficulty not in [d.value for d in DifficultyLevel]:
            errors.append(f"Invalid difficulty: {scenario.difficulty}")
        
        if scenario.priority not in [p.value for p in PriorityLevel]:
            errors.append(f"Invalid priority: {scenario.priority}")
        
        return errors
    
    def _validate_field_formats(
        self,
        scenario: GeneratedScenario
    ) -> Tuple[List[str], List[str]]:
        """Validate field formats and lengths."""
        errors = []
        warnings = []
        
        # Title length
        if scenario.title:
            title_len = len(scenario.title)
            if title_len < self.min_title_length:
                errors.append(f"Title too short: {title_len} chars (min: {self.min_title_length})")
            elif title_len > self.max_title_length:
                warnings.append(f"Title very long: {title_len} chars (max: {self.max_title_length})")
        
        # Description length
        if scenario.description:
            desc_len = len(scenario.description)
            if desc_len < self.min_description_length:
                errors.append(f"Description too short: {desc_len} chars (min: {self.min_description_length})")
        
        # User input length
        if scenario.user_input:
            input_len = len(scenario.user_input)
            if input_len < self.min_user_input_length:
                errors.append(f"User input too short: {input_len} chars (min: {self.min_user_input_length})")
        
        # Tags
        if scenario.tags and len(scenario.tags) > 20:
            warnings.append(f"Too many tags: {len(scenario.tags)} (recommended max: 20)")
        
        # Target tools
        if scenario.target_tools and len(scenario.target_tools) > 10:
            warnings.append(f"Too many target tools: {len(scenario.target_tools)} (recommended max: 10)")
        
        return errors, warnings
    
    def _validate_expected_behaviors(
        self,
        scenario: GeneratedScenario
    ) -> Tuple[List[str], List[str]]:
        """Validate expected behaviors."""
        errors = []
        warnings = []
        
        if not scenario.expected_behavior:
            return errors, warnings
        
        # Check for at least one behavior
        if len(scenario.expected_behavior) == 0:
            errors.append("Must have at least one expected behavior")
        
        # Validate each behavior
        for idx, behavior in enumerate(scenario.expected_behavior):
            # Check behavior type
            valid_types = [t.value for t in ExpectedBehaviorType]
            if behavior.behavior_type.value not in valid_types:
                errors.append(f"Behavior {idx}: Invalid type '{behavior.behavior_type}'")
            
            # Check description
            if not behavior.description or not behavior.description.strip():
                errors.append(f"Behavior {idx}: Missing description")
            
            # Tool-specific behaviors should specify tool name
            if behavior.behavior_type in [
                ExpectedBehaviorType.MUST_USE_TOOL,
                ExpectedBehaviorType.MUST_NOT_USE_TOOL
            ]:
                if not behavior.tool_name:
                    warnings.append(f"Behavior {idx}: Tool behavior without tool_name specified")
        
        # Check for conflicting behaviors
        behavior_types = [b.behavior_type for b in scenario.expected_behavior]
        if (ExpectedBehaviorType.MUST_RESPOND in behavior_types and 
            ExpectedBehaviorType.MUST_REFUSE in behavior_types):
            errors.append("Conflicting behaviors: MUST_RESPOND and MUST_REFUSE")
        
        return errors, warnings
    
    def _validate_validation_rules(self, scenario: GeneratedScenario) -> List[str]:
        """Validate validation rules."""
        errors = []
        
        if not scenario.validation_rules:
            return errors
        
        # Check for at least one rule
        if len(scenario.validation_rules) == 0:
            errors.append("Must have at least one validation rule")
        
        # Validate each rule
        for idx, rule in enumerate(scenario.validation_rules):
            if not rule.rule_type or not rule.rule_type.strip():
                errors.append(f"Validation rule {idx}: Missing rule_type")
            
            if not rule.condition or not rule.condition.strip():
                errors.append(f"Validation rule {idx}: Missing condition")
            
            if rule.expected_value is None:
                errors.append(f"Validation rule {idx}: Missing expected_value")
        
        return errors
    
    def _validate_conversation_steps(
        self,
        scenario: GeneratedScenario
    ) -> Tuple[List[str], List[str]]:
        """Validate conversation steps structure."""
        errors = []
        warnings = []
        
        if not scenario.conversation_steps:
            # Single-turn is OK
            return errors, warnings
        
        # Multi-turn validation
        if len(scenario.conversation_steps) < 2:
            warnings.append("conversation_steps present but only 1 turn (use user_input for single-turn)")
        
        # Validate turn structure
        for idx, turn in enumerate(scenario.conversation_steps):
            if turn.turn_number != idx + 1:
                errors.append(f"Turn {idx}: Invalid turn_number (expected {idx + 1}, got {turn.turn_number})")
            
            if not turn.speaker or turn.speaker not in ["user", "agent"]:
                errors.append(f"Turn {idx}: Invalid speaker (must be 'user' or 'agent')")
            
            if not turn.message or not turn.message.strip():
                errors.append(f"Turn {idx}: Missing message")
        
        # Check alternating speakers
        speakers = [turn.speaker for turn in scenario.conversation_steps]
        for i in range(len(speakers) - 1):
            if speakers[i] == speakers[i + 1]:
                warnings.append(f"Turns {i + 1} and {i + 2}: Same speaker twice in a row")
        
        # First turn should be user
        if scenario.conversation_steps and scenario.conversation_steps[0].speaker != "user":
            warnings.append("First turn should be from user")
        
        return errors, warnings
    
    def _validate_quality_score(
        self,
        scenario: GeneratedScenario
    ) -> Tuple[List[str], List[str]]:
        """Validate quality score and rationale."""
        errors = []
        warnings = []
        
        # Check range
        if scenario.quality_score < 0.0 or scenario.quality_score > 1.0:
            errors.append(f"Quality score out of range: {scenario.quality_score} (must be 0.0-1.0)")
        
        # Check threshold
        if scenario.quality_score < self.min_quality_score:
            errors.append(f"Quality score too low: {scenario.quality_score} (min: {self.min_quality_score})")
        
        # Check for rationale
        if not scenario.quality_rationale or len(scenario.quality_rationale) < 10:
            warnings.append("Missing or very short quality_rationale")
        
        return errors, warnings
    
    def _validate_category_consistency(self, scenario: GeneratedScenario) -> List[str]:
        """Check consistency between category, difficulty, and risk level."""
        warnings = []
        
        # Safety-critical scenarios should have high priority
        if scenario.risk_level in ["high", "critical"]:
            if scenario.priority not in ["high", "critical"]:
                warnings.append(f"Risk level '{scenario.risk_level}' but priority is '{scenario.priority}'")
        
        # Adversarial scenarios should not be easy
        if scenario.difficulty == "easy" and scenario.risk_level in ["high", "critical"]:
            warnings.append("Adversarial/critical scenario marked as 'easy' difficulty")
        
        return warnings
    
    # ========================================================================
    # Scoring
    # ========================================================================

    def _calculate_validation_score(
        self,
        errors: List[str],
        warnings: List[str],
        quality_score: float
    ) -> float:
        """
        Calculate overall validation score.
        
        Returns: 0.0 to 1.0 score
        """
        # Start with LLM's quality score
        score = quality_score
        
        # Penalize for errors (each error reduces score)
        error_penalty = len(errors) * 0.1
        score = max(0.0, score - error_penalty)
        
        # Small penalty for warnings
        warning_penalty = len(warnings) * 0.02
        score = max(0.0, score - warning_penalty)
        
        return round(score, 3)
    
    # ========================================================================
    # Bulk Operations
    # ========================================================================

    def filter_valid_scenarios(
        self,
        scenarios: List[GeneratedScenario],
        strict: bool = True
    ) -> List[GeneratedScenario]:
        """Filter and return only valid scenarios."""
        valid, _ = self.validate_batch(scenarios, strict=strict)
        return valid
    
    def get_validation_report(
        self,
        scenarios: List[GeneratedScenario],
        strict: bool = True
    ) -> Dict[str, Any]:
        """Generate a validation report for a batch of scenarios."""
        valid, rejected = self.validate_batch(scenarios, strict=strict)
        
        total = len(scenarios)
        valid_count = len(valid)
        rejected_count = len(rejected)
        
        # Aggregate errors and warnings
        all_errors = []
        all_warnings = []
        for _, result in rejected:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        # Error frequency
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        return {
            "total_scenarios": total,
            "valid_count": valid_count,
            "rejected_count": rejected_count,
            "validation_rate": round(valid_count / total, 3) if total > 0 else 0.0,
            "error_counts": error_counts,
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "rejected_details": [
                {
                    "title": scenario.title,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "score": result.score
                }
                for scenario, result in rejected
            ]
        }
