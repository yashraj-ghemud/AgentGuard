"""
Scenario Deduplication Service

Detects and removes duplicate or near-duplicate scenarios.
"""
from typing import List, Set, Tuple, Dict
from uuid import UUID
import re
from difflib import SequenceMatcher

from modules.scenario_generation.domain.schemas import GeneratedScenario
from modules.scenario_generation.domain.models import Scenario


class DeduplicationService:
    """
    Service for detecting duplicate scenarios.
    
    Uses multiple strategies:
    - Exact text matching
    - Normalized text matching (case-insensitive, whitespace-normalized)
    - Semantic similarity (fuzzy matching)
    - Intent similarity (conversation patterns)
    """

    def __init__(self):
        self.exact_similarity_threshold = 1.0  # Exact match
        self.high_similarity_threshold = 0.9  # 90% similar -> likely duplicate
        self.moderate_similarity_threshold = 0.75  # 75% similar -> review needed
    
    # ========================================================================
    # Main Deduplication API
    # ========================================================================

    def deduplicate_generated_scenarios(
        self,
        scenarios: List[GeneratedScenario],
        strict: bool = False
    ) -> Tuple[List[GeneratedScenario], List[Tuple[GeneratedScenario, str]]]:
        """
        Remove duplicates from a list of generated scenarios.
        
        Args:
            scenarios: List of scenarios to deduplicate
            strict: If True, use moderate threshold (75%). If False, use high threshold (90%)
        
        Returns:
            (unique_scenarios, duplicates_with_reasons)
        """
        threshold = self.moderate_similarity_threshold if strict else self.high_similarity_threshold
        
        unique = []
        duplicates = []
        seen_signatures = set()
        
        for scenario in scenarios:
            # Check if duplicate
            is_duplicate, duplicate_of, reason = self._is_duplicate(
                scenario,
                unique,
                seen_signatures,
                threshold
            )
            
            if is_duplicate:
                duplicates.append((scenario, f"Duplicate of '{duplicate_of}': {reason}"))
            else:
                unique.append(scenario)
                # Add signatures
                signature = self._generate_signature(scenario)
                seen_signatures.add(signature)
        
        return unique, duplicates
    
    def deduplicate_database_scenarios(
        self,
        scenarios: List[Scenario],
        strict: bool = False
    ) -> Tuple[List[Scenario], List[Tuple[Scenario, UUID, str]]]:
        """
        Remove duplicates from database scenarios.
        
        Returns:
            (unique_scenarios, duplicates_with_original_id_and_reasons)
        """
        threshold = self.moderate_similarity_threshold if strict else self.high_similarity_threshold
        
        unique = []
        duplicates = []
        seen_signatures = set()
        
        for scenario in scenarios:
            # Check if duplicate
            is_duplicate, duplicate_of_idx, reason = self._is_database_duplicate(
                scenario,
                unique,
                seen_signatures,
                threshold
            )
            
            if is_duplicate:
                original_id = unique[duplicate_of_idx].id
                duplicates.append((scenario, original_id, reason))
            else:
                unique.append(scenario)
                signature = self._generate_database_signature(scenario)
                seen_signatures.add(signature)
        
        return unique, duplicates
    
    # ========================================================================
    # Duplicate Detection (Generated Scenarios)
    # ========================================================================

    def _is_duplicate(
        self,
        scenario: GeneratedScenario,
        existing: List[GeneratedScenario],
        seen_signatures: Set[str],
        threshold: float
    ) -> Tuple[bool, str, str]:
        """
        Check if scenario is a duplicate of any existing scenario.
        
        Returns:
            (is_duplicate, duplicate_of_title, reason)
        """
        # 1. Exact signature match (fastest)
        signature = self._generate_signature(scenario)
        if signature in seen_signatures:
            return True, "exact match", "Exact signature match"
        
        # 2. Check similarity with each existing scenario
        for existing_scenario in existing:
            similarity, reason = self._calculate_similarity(scenario, existing_scenario)
            
            if similarity >= threshold:
                return True, existing_scenario.title, f"Similarity: {similarity:.2%} - {reason}"
        
        return False, "", ""
    
    def _generate_signature(self, scenario: GeneratedScenario) -> str:
        """
        Generate a unique signature for a scenario.
        
        Signature combines normalized title and user input.
        """
        title_norm = self._normalize_text(scenario.title)
        input_norm = self._normalize_text(scenario.user_input)
        return f"{title_norm}::{input_norm}"
    
    def _calculate_similarity(
        self,
        scenario1: GeneratedScenario,
        scenario2: GeneratedScenario
    ) -> Tuple[float, str]:
        """
        Calculate similarity between two scenarios.
        
        Returns:
            (similarity_score, reason)
        """
        # Multiple similarity metrics
        
        # 1. Title similarity
        title_sim = self._text_similarity(scenario1.title, scenario2.title)
        
        # 2. User input similarity
        input_sim = self._text_similarity(scenario1.user_input, scenario2.user_input)
        
        # 3. Description similarity
        desc_sim = self._text_similarity(scenario1.description, scenario2.description)
        
        # 4. Target tools overlap
        tools1 = set(scenario1.target_tools)
        tools2 = set(scenario2.target_tools)
        if tools1 and tools2:
            tool_sim = len(tools1 & tools2) / len(tools1 | tools2)
        else:
            tool_sim = 0.0
        
        # 5. Expected behavior similarity
        behavior_types1 = {b.behavior_type for b in scenario1.expected_behavior}
        behavior_types2 = {b.behavior_type for b in scenario2.expected_behavior}
        if behavior_types1 and behavior_types2:
            behavior_sim = len(behavior_types1 & behavior_types2) / len(behavior_types1 | behavior_types2)
        else:
            behavior_sim = 0.0
        
        # Weighted average (user input and title are most important)
        weights = {
            "title": 0.25,
            "input": 0.40,
            "description": 0.15,
            "tools": 0.10,
            "behavior": 0.10
        }
        
        overall_similarity = (
            title_sim * weights["title"] +
            input_sim * weights["input"] +
            desc_sim * weights["description"] +
            tool_sim * weights["tools"] +
            behavior_sim * weights["behavior"]
        )
        
        # Determine reason
        if input_sim > 0.9:
            reason = "Very similar user input"
        elif title_sim > 0.9:
            reason = "Very similar title"
        elif desc_sim > 0.9:
            reason = "Very similar description"
        elif tool_sim > 0.8 and behavior_sim > 0.8:
            reason = "Same tools and behaviors"
        else:
            reason = "Overall similarity"
        
        return overall_similarity, reason
    
    # ========================================================================
    # Duplicate Detection (Database Scenarios)
    # ========================================================================

    def _is_database_duplicate(
        self,
        scenario: Scenario,
        existing: List[Scenario],
        seen_signatures: Set[str],
        threshold: float
    ) -> Tuple[bool, int, str]:
        """
        Check if database scenario is a duplicate.
        
        Returns:
            (is_duplicate, index_of_original, reason)
        """
        # 1. Exact signature match
        signature = self._generate_database_signature(scenario)
        if signature in seen_signatures:
            # Find the original
            for idx, existing_scenario in enumerate(existing):
                if self._generate_database_signature(existing_scenario) == signature:
                    return True, idx, "Exact signature match"
        
        # 2. Similarity check
        for idx, existing_scenario in enumerate(existing):
            similarity, reason = self._calculate_database_similarity(scenario, existing_scenario)
            
            if similarity >= threshold:
                return True, idx, f"Similarity: {similarity:.2%} - {reason}"
        
        return False, -1, ""
    
    def _generate_database_signature(self, scenario: Scenario) -> str:
        """Generate signature for database scenario."""
        title_norm = self._normalize_text(scenario.title)
        input_norm = self._normalize_text(scenario.user_input)
        return f"{title_norm}::{input_norm}"
    
    def _calculate_database_similarity(
        self,
        scenario1: Scenario,
        scenario2: Scenario
    ) -> Tuple[float, str]:
        """Calculate similarity between database scenarios."""
        # Similar to _calculate_similarity but for database models
        
        title_sim = self._text_similarity(scenario1.title, scenario2.title)
        input_sim = self._text_similarity(scenario1.user_input, scenario2.user_input)
        desc_sim = self._text_similarity(scenario1.description, scenario2.description)
        
        # Tools
        tools1 = set(scenario1.target_tools) if scenario1.target_tools else set()
        tools2 = set(scenario2.target_tools) if scenario2.target_tools else set()
        if tools1 and tools2:
            tool_sim = len(tools1 & tools2) / len(tools1 | tools2)
        else:
            tool_sim = 0.0
        
        # Weighted average
        overall_similarity = (
            title_sim * 0.25 +
            input_sim * 0.40 +
            desc_sim * 0.15 +
            tool_sim * 0.20
        )
        
        if input_sim > 0.9:
            reason = "Very similar user input"
        elif title_sim > 0.9:
            reason = "Very similar title"
        else:
            reason = "Overall similarity"
        
        return overall_similarity, reason
    
    # ========================================================================
    # Text Processing Utilities
    # ========================================================================

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        - Convert to lowercase
        - Remove extra whitespace
        - Remove punctuation
        - Sort words (for bag-of-words comparison)
        """
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using SequenceMatcher.
        
        Returns: 0.0 to 1.0 similarity score
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize
        norm1 = self._normalize_text(text1)
        norm2 = self._normalize_text(text2)
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    # ========================================================================
    # Statistics
    # ========================================================================

    def get_deduplication_stats(
        self,
        original_count: int,
        unique_count: int,
        duplicates: List
    ) -> Dict:
        """Generate deduplication statistics."""
        duplicate_count = len(duplicates)
        dedup_rate = (duplicate_count / original_count * 100) if original_count > 0 else 0.0
        
        return {
            "original_count": original_count,
            "unique_count": unique_count,
            "duplicate_count": duplicate_count,
            "deduplication_rate": round(dedup_rate, 2),
            "duplicate_details": [
                {
                    "title": dup[0].title if hasattr(dup[0], 'title') else "Unknown",
                    "reason": dup[1] if len(dup) >= 2 else "Unknown"
                }
                for dup in duplicates[:10]  # Show first 10
            ]
        }
