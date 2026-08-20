"""
Scenario Prioritization Service

Intelligently ranks scenarios based on risk, coverage, and value.
"""
from typing import List, Dict, Any
from dataclasses import dataclass

from modules.scenario_generation.domain.models import Scenario
from modules.scenario_generation.domain.schemas import GeneratedScenario
from shared.scenario_types import PriorityLevel


@dataclass
class PrioritizationScore:
    """Prioritization score breakdown."""
    total_score: float  # 0.0 to 100.0
    risk_score: float  # 0.0 to 30.0
    coverage_score: float  # 0.0 to 25.0
    quality_score: float  # 0.0 to 25.0
    novelty_score: float  # 0.0 to 20.0
    priority_level: str  # critical, high, medium, low
    rationale: str


class ScenarioPrioritizationService:
    """
    Service for prioritizing scenarios.
    
    Prioritization factors:
    1. Risk level (30%) - Higher risk scenarios are more important
    2. Coverage (25%) - Scenarios covering untested tools/behaviors
    3. Quality (25%) - LLM quality score + validation score
    4. Novelty (20%) - Unique or creative test approaches
    """

    def __init__(self):
        # Scoring weights
        self.weights = {
            "risk": 0.30,
            "coverage": 0.25,
            "quality": 0.25,
            "novelty": 0.20
        }
        
        # Priority thresholds
        self.critical_threshold = 80.0
        self.high_threshold = 60.0
        self.medium_threshold = 40.0
    
    # ========================================================================
    # Main Prioritization API
    # ========================================================================

    def prioritize_generated_scenarios(
        self,
        scenarios: List[GeneratedScenario],
        existing_coverage: Dict[str, int] = None
    ) -> List[tuple[GeneratedScenario, PrioritizationScore]]:
        """
        Prioritize a list of generated scenarios.
        
        Args:
            scenarios: Scenarios to prioritize
            existing_coverage: Dict of {tool_name: count} for coverage scoring
        
        Returns:
            List of (scenario, score) sorted by priority (highest first)
        """
        if existing_coverage is None:
            existing_coverage = {}
        
        scored_scenarios = []
        
        for scenario in scenarios:
            score = self._calculate_priority_score(scenario, existing_coverage)
            scored_scenarios.append((scenario, score))
        
        # Sort by total score (descending)
        scored_scenarios.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return scored_scenarios
    
    def prioritize_database_scenarios(
        self,
        scenarios: List[Scenario],
        existing_coverage: Dict[str, int] = None
    ) -> List[tuple[Scenario, PrioritizationScore]]:
        """
        Prioritize database scenarios.
        
        Returns:
            List of (scenario, score) sorted by priority (highest first)
        """
        if existing_coverage is None:
            existing_coverage = {}
        
        scored_scenarios = []
        
        for scenario in scenarios:
            score = self._calculate_database_priority_score(scenario, existing_coverage)
            scored_scenarios.append((scenario, score))
        
        # Sort by total score (descending)
        scored_scenarios.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return scored_scenarios
    
    def assign_priorities(
        self,
        scenarios: List[GeneratedScenario],
        existing_coverage: Dict[str, int] = None
    ) -> List[GeneratedScenario]:
        """
        Assign priority levels to scenarios based on scoring.
        
        Modifies scenarios in-place and returns them.
        """
        scored = self.prioritize_generated_scenarios(scenarios, existing_coverage)
        
        for scenario, score in scored:
            scenario.priority = score.priority_level
        
        return scenarios
    
    # ========================================================================
    # Scoring Logic (Generated Scenarios)
    # ========================================================================

    def _calculate_priority_score(
        self,
        scenario: GeneratedScenario,
        existing_coverage: Dict[str, int]
    ) -> PrioritizationScore:
        """Calculate priority score for a generated scenario."""
        
        # 1. Risk Score (0-30 points)
        risk_score = self._calculate_risk_score(scenario.risk_level)
        
        # 2. Coverage Score (0-25 points)
        coverage_score = self._calculate_coverage_score(
            scenario.target_tools,
            existing_coverage
        )
        
        # 3. Quality Score (0-25 points)
        quality_score = scenario.quality_score * 25.0
        
        # 4. Novelty Score (0-20 points)
        novelty_score = self._calculate_novelty_score(scenario)
        
        # Total score (0-100)
        total_score = (
            risk_score +
            coverage_score +
            quality_score +
            novelty_score
        )
        
        # Determine priority level
        if total_score >= self.critical_threshold:
            priority_level = PriorityLevel.CRITICAL.value
        elif total_score >= self.high_threshold:
            priority_level = PriorityLevel.HIGH.value
        elif total_score >= self.medium_threshold:
            priority_level = PriorityLevel.MEDIUM.value
        else:
            priority_level = PriorityLevel.LOW.value
        
        # Generate rationale
        rationale = self._generate_rationale(
            risk_score, coverage_score, quality_score, novelty_score
        )
        
        return PrioritizationScore(
            total_score=round(total_score, 2),
            risk_score=round(risk_score, 2),
            coverage_score=round(coverage_score, 2),
            quality_score=round(quality_score, 2),
            novelty_score=round(novelty_score, 2),
            priority_level=priority_level,
            rationale=rationale
        )
    
    def _calculate_risk_score(self, risk_level: str) -> float:
        """
        Calculate risk score (0-30 points).
        
        Higher risk = higher priority.
        """
        risk_scores = {
            "critical": 30.0,
            "high": 22.0,
            "medium": 14.0,
            "low": 6.0
        }
        return risk_scores.get(risk_level.lower(), 10.0)
    
    def _calculate_coverage_score(
        self,
        target_tools: List[str],
        existing_coverage: Dict[str, int]
    ) -> float:
        """
        Calculate coverage score (0-25 points).
        
        Scenarios targeting less-covered tools get higher scores.
        """
        if not target_tools:
            return 10.0  # Neutral score
        
        # Calculate average coverage for target tools
        total_coverage = 0
        for tool in target_tools:
            coverage = existing_coverage.get(tool, 0)
            total_coverage += coverage
        
        avg_coverage = total_coverage / len(target_tools)
        
        # Inverse relationship: less coverage = higher score
        if avg_coverage == 0:
            return 25.0  # Maximum for uncovered tools
        elif avg_coverage < 3:
            return 20.0
        elif avg_coverage < 6:
            return 15.0
        elif avg_coverage < 10:
            return 10.0
        else:
            return 5.0  # Tool already well-covered
    
    def _calculate_novelty_score(self, scenario: GeneratedScenario) -> float:
        """
        Calculate novelty score (0-20 points).
        
        Based on creativity indicators:
        - Multi-turn conversations
        - Complex validation rules
        - Multiple expected behaviors
        - Unique category combinations
        """
        score = 0.0
        
        # Multi-turn bonus (up to 5 points)
        if scenario.conversation_steps and len(scenario.conversation_steps) >= 2:
            score += min(5.0, len(scenario.conversation_steps))
        
        # Validation complexity bonus (up to 5 points)
        if scenario.validation_rules:
            score += min(5.0, len(scenario.validation_rules))
        
        # Expected behavior complexity (up to 5 points)
        if scenario.expected_behavior:
            score += min(5.0, len(scenario.expected_behavior))
        
        # Category-specific bonuses (up to 5 points)
        if scenario.difficulty == "hard":
            score += 3.0
        elif scenario.difficulty == "expert":
            score += 5.0
        
        return min(20.0, score)
    
    # ========================================================================
    # Scoring Logic (Database Scenarios)
    # ========================================================================

    def _calculate_database_priority_score(
        self,
        scenario: Scenario,
        existing_coverage: Dict[str, int]
    ) -> PrioritizationScore:
        """Calculate priority score for a database scenario."""
        
        # Similar to _calculate_priority_score but for database models
        
        # 1. Risk Score
        risk_score = self._calculate_risk_score(scenario.risk_level)
        
        # 2. Coverage Score
        coverage_score = self._calculate_coverage_score(
            scenario.target_tools or [],
            existing_coverage
        )
        
        # 3. Quality Score
        quality_score = (scenario.quality_score or 0.5) * 25.0
        
        # 4. Novelty Score
        novelty_score = self._calculate_database_novelty_score(scenario)
        
        # Total
        total_score = (
            risk_score +
            coverage_score +
            quality_score +
            novelty_score
        )
        
        # Priority level
        if total_score >= self.critical_threshold:
            priority_level = PriorityLevel.CRITICAL.value
        elif total_score >= self.high_threshold:
            priority_level = PriorityLevel.HIGH.value
        elif total_score >= self.medium_threshold:
            priority_level = PriorityLevel.MEDIUM.value
        else:
            priority_level = PriorityLevel.LOW.value
        
        rationale = self._generate_rationale(
            risk_score, coverage_score, quality_score, novelty_score
        )
        
        return PrioritizationScore(
            total_score=round(total_score, 2),
            risk_score=round(risk_score, 2),
            coverage_score=round(coverage_score, 2),
            quality_score=round(quality_score, 2),
            novelty_score=round(novelty_score, 2),
            priority_level=priority_level,
            rationale=rationale
        )
    
    def _calculate_database_novelty_score(self, scenario: Scenario) -> float:
        """Calculate novelty score for database scenario."""
        score = 0.0
        
        # Multi-turn
        if scenario.conversation_steps and len(scenario.conversation_steps) >= 2:
            score += min(5.0, len(scenario.conversation_steps))
        
        # Validation rules
        if scenario.validation_rules:
            score += min(5.0, len(scenario.validation_rules))
        
        # Expected behaviors
        if scenario.expected_behavior:
            score += min(5.0, len(scenario.expected_behavior))
        
        # Difficulty
        if scenario.difficulty == "hard":
            score += 3.0
        elif scenario.difficulty == "expert":
            score += 5.0
        
        return min(20.0, score)
    
    # ========================================================================
    # Utilities
    # ========================================================================

    def _generate_rationale(
        self,
        risk_score: float,
        coverage_score: float,
        quality_score: float,
        novelty_score: float
    ) -> str:
        """Generate human-readable rationale for prioritization."""
        reasons = []
        
        if risk_score >= 22:
            reasons.append("high/critical risk")
        if coverage_score >= 20:
            reasons.append("targets uncovered tools")
        if quality_score >= 20:
            reasons.append("high quality")
        if novelty_score >= 15:
            reasons.append("novel/complex scenario")
        
        if reasons:
            return "Prioritized due to: " + ", ".join(reasons)
        else:
            return "Standard priority scenario"
    
    def get_prioritization_stats(
        self,
        scored_scenarios: List[tuple[Any, PrioritizationScore]]
    ) -> Dict[str, Any]:
        """Generate prioritization statistics."""
        if not scored_scenarios:
            return {
                "total_scenarios": 0,
                "priority_distribution": {},
                "average_score": 0.0
            }
        
        # Count by priority
        priority_counts = {}
        total_score = 0.0
        
        for _, score in scored_scenarios:
            priority = score.priority_level
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            total_score += score.total_score
        
        return {
            "total_scenarios": len(scored_scenarios),
            "priority_distribution": priority_counts,
            "average_score": round(total_score / len(scored_scenarios), 2),
            "highest_score": round(scored_scenarios[0][1].total_score, 2) if scored_scenarios else 0.0,
            "lowest_score": round(scored_scenarios[-1][1].total_score, 2) if scored_scenarios else 0.0
        }
