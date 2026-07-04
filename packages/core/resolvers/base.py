from __future__ import annotations

"""
Base resolver interface.

All resolvers implement this interface to ensure consistent behavior
and enable pipeline composition.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.resolver_models import DOMElement, ResolverCandidate, ActionNode


class BaseResolver(ABC):
    """
    Abstract base class for all resolvers.
    
    Resolvers do not execute actions. They only reason about selection.
    Each resolver must be:
    - Deterministic: Same inputs always produce same outputs
    - Explainable: Must provide reasons for scores
    - Pure: No side effects, no network calls
    """
    
    name: str = "base"
    
    @abstractmethod
    def resolve(
        self,
        candidates: list["DOMElement"],
        action: "ActionNode",
        context: dict,
    ) -> list["ResolverCandidate"]:
        """
        Resolve and score candidates.
        
        Args:
            candidates: List of DOM elements to evaluate
            action: The action being resolved
            context: Additional context (page URL, previous elements, etc.)
        
        Returns:
            List of ResolverCandidate with scores and reasons.
            May be empty if no candidates pass.
        """
        pass
    
    def filter_candidates(
        self,
        candidates: list["ResolverCandidate"],
        min_score: float = 0.0,
    ) -> list["ResolverCandidate"]:
        """Filter candidates below minimum score threshold."""
        return [c for c in candidates if c.score >= min_score]
    
    def rank_candidates(
        self,
        candidates: list["ResolverCandidate"],
    ) -> list["ResolverCandidate"]:
        """Sort candidates by score descending."""
        return sorted(candidates, key=lambda c: c.score, reverse=True)
