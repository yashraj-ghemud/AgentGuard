"""Transparent, dependency-free groundedness analysis.

This module intentionally does not claim to prove truth.  It checks whether an
agent answer is lexically supported by caller-provided reference evidence and
whether explicitly forbidden claims appear.  The limitation is returned to
callers so the result is not misrepresented as a perfect hallucination oracle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from modules.evaluation.domain.schemas import GroundingSpec

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'_-]*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by",
    "for", "from", "has", "have", "he", "her", "hers", "him", "his", "i",
    "in", "is", "it", "its", "of", "on", "or", "our", "she", "that", "the",
    "their", "them", "there", "these", "they", "this", "to", "was", "were",
    "what", "when", "where", "which", "who", "why", "with", "you", "your",
}

_ABSTENTION_MARKERS = (
    "i don't know",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "i cannot verify",
    "i can't verify",
    "cannot verify",
    "can't verify",
    "not enough information",
    "insufficient information",
    "i don't have enough information",
    "i do not have enough information",
    "i cannot determine",
    "i can't determine",
    "unable to determine",
)


@dataclass(frozen=True)
class GroundingEvidence:
    """Evidence for one answer sentence."""

    claim: str
    evidence: str | None
    overlap: float
    supported: bool


@dataclass(frozen=True)
class GroundingAnalysis:
    """Explainable groundedness result."""

    grounded: bool
    score: float
    evidence: tuple[GroundingEvidence, ...]
    unsupported_sentences: tuple[str, ...]
    missing_required_facts: tuple[str, ...]
    forbidden_claims_detected: tuple[str, ...]
    abstention_ok: bool | None
    caveat: str


def analyze_grounding(answer: str, spec: GroundingSpec) -> GroundingAnalysis:
    """Evaluate whether an answer is supported by supplied reference evidence."""
    normalized_answer = answer.strip()
    reference_sentences = _sentences(spec.reference_context)
    answer_sentences = _sentences(normalized_answer)

    evidence: list[GroundingEvidence] = []
    for claim in answer_sentences:
        if not claim.strip():
            continue
        best_sentence, best_overlap = _best_reference_match(claim, reference_sentences)
        evidence.append(
            GroundingEvidence(
                claim=claim,
                evidence=best_sentence,
                overlap=round(best_overlap, 4),
                supported=best_overlap >= spec.min_sentence_overlap,
            )
        )

    unsupported = tuple(item.claim for item in evidence if not item.supported)

    missing_required = tuple(
        fact for fact in spec.required_facts if not _contains_fact(normalized_answer, fact)
    )
    forbidden = tuple(
        claim for claim in spec.forbidden_claims if _contains_fact(normalized_answer, claim)
    )

    abstention_ok: bool | None = None
    if not spec.answerable and spec.require_abstention_when_unanswerable:
        lower_answer = normalized_answer.lower()
        abstention_ok = any(marker in lower_answer for marker in _ABSTENTION_MARKERS)

    total_checks = max(1, len(evidence) + len(spec.required_facts) + len(spec.forbidden_claims) + (1 if abstention_ok is not None else 0))
    passed_checks = sum(1 for item in evidence if item.supported)
    passed_checks += len(spec.required_facts) - len(missing_required)
    passed_checks += len(spec.forbidden_claims) - len(forbidden)
    if abstention_ok is not None and abstention_ok:
        passed_checks += 1

    score = round(max(0.0, min(1.0, passed_checks / total_checks)), 4)
    grounded = (
        len(unsupported) <= spec.max_unsupported_sentences
        and not missing_required
        and not forbidden
        and (abstention_ok is not False)
    )

    return GroundingAnalysis(
        grounded=grounded,
        score=score,
        evidence=tuple(evidence),
        unsupported_sentences=unsupported,
        missing_required_facts=missing_required,
        forbidden_claims_detected=forbidden,
        abstention_ok=abstention_ok,
        caveat=(
            "Lexical groundedness check only: it compares answer text with supplied evidence and explicit claims. "
            "It does not establish real-world truth and should be paired with semantic/NLI or human review for high-stakes use."
        ),
    )


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_RE.split(text or "") if part.strip()]


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in _WORD_RE.findall(text)
        if token.lower() not in _STOP_WORDS and len(token) > 1
    }


def _best_reference_match(claim: str, reference_sentences: Iterable[str]) -> tuple[str | None, float]:
    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return None, 0.0

    best_sentence: str | None = None
    best_overlap = 0.0
    for reference in reference_sentences:
        reference_tokens = _tokens(reference)
        if not reference_tokens:
            continue
        intersection = len(claim_tokens & reference_tokens)
        union = len(claim_tokens | reference_tokens)
        score = intersection / union if union else 0.0
        if score > best_overlap:
            best_overlap = score
            best_sentence = reference
    return best_sentence, best_overlap


def _contains_fact(answer: str, fact: str) -> bool:
    normalized_answer = " ".join(answer.lower().split())
    normalized_fact = " ".join(str(fact).lower().split())
    return bool(normalized_fact) and normalized_fact in normalized_answer
