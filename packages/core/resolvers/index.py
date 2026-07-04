from __future__ import annotations

"""
Index Resolver - Last resort for repeated elements.

This resolver answers: "Is this element identified by its position within a list or grid?"

This is a LAST RESORT resolver. Used only when:
- Multiple identical candidates remain after other resolvers
- Repeated structures are detected (lists, grids)
- An explicit index is provided in the action target

If no index is provided and multiple candidates match, this resolver FAILS LOUDLY.
"""
from typing import Optional, Dict, List, Union

from .base import BaseResolver
from ..models.resolver_models import DOMElement, ResolverCandidate, ActionNode


# Tags that commonly contain repeated children
CONTAINER_TAGS = {"ul", "ol", "table", "tbody", "thead", "nav", "menu"}

# Roles that indicate repeated structures
REPEATING_ROLES = {"list", "listbox", "menu", "menubar", "tablist", "grid", "row"}


class IndexResolver(BaseResolver):
    """
    Index resolver handles repeated elements using positional matching.
    
    This is the last resolver in the pipeline. It's used when semantic,
    context, and selector resolvers cannot distinguish between candidates.
    
    Philosophy: If we can't distinguish elements, FAIL LOUDLY.
    """
    
    name = "index"
    
    def __init__(self, dom_lookup: Optional[Dict[str, DOMElement]] = None):
        """
        Initialize with optional DOM lookup for sibling detection.
        
        Args:
            dom_lookup: Dict mapping node_id to DOMElement
        """
        self.dom_lookup = dom_lookup or {}
    
    def set_dom_lookup(self, dom_lookup: Dict[str, DOMElement]) -> None:
        """Update the DOM lookup table."""
        self.dom_lookup = dom_lookup
    
    def resolve(
        self,
        candidates: Union[List[DOMElement], List[ResolverCandidate]],
        action: ActionNode,
        context: dict,
    ) -> List[ResolverCandidate]:
        """
        Resolve candidates using index-based matching.
        
        If an index is provided, select the candidate at that position
        using DOM-order sibling index (not pipeline position).
        If no index and multiple candidates exist, fail loudly.
        """
        results = []
        
        # Convert to ResolverCandidates if needed
        resolver_candidates = []
        for candidate in candidates:
            if isinstance(candidate, ResolverCandidate):
                resolver_candidates.append(candidate)
            else:
                resolver_candidates.append(ResolverCandidate(
                    element=candidate,
                    score=0.0,
                    reasons=[],
                ))
        
        # If only one candidate, just return it
        if len(resolver_candidates) == 1:
            resolver_candidates[0].reasons.append("single_candidate")
            return resolver_candidates
        
        # If no candidates, nothing to do
        if len(resolver_candidates) == 0:
            return []
        
        # Check if index is provided
        target_index = action.target.index
        
        if target_index is not None:
            # Use explicit index — match against DOM sibling_index, not list position
            return self._resolve_by_sibling_index(resolver_candidates, target_index)
        else:
            # No index provided - detect repetition and fail loudly
            return self._handle_ambiguity(resolver_candidates, context)
    
    def _resolve_by_sibling_index(
        self,
        candidates: List[ResolverCandidate],
        index: int,
    ) -> List[ResolverCandidate]:
        """
        Select candidate whose DOM sibling_index matches the target index.
        
        Falls back to list-position indexing if no sibling_index match.
        """
        # First try: match by DOM sibling_index
        for candidate in candidates:
            if candidate.element.sibling_index == index:
                candidate.score += 0.5
                candidate.reasons.append(f"sibling_index_match:{index}")
                return [candidate]
        
        # Fallback: use list position (legacy behavior)
        if 0 <= index < len(candidates):
            selected = candidates[index]
            selected.score += 0.3
            selected.reasons.append(f"positional_index_match:{index}")
            return [selected]
        
        # Index out of range
        for candidate in candidates:
            candidate.reasons.append(f"index_out_of_range:{index}")
        return candidates
    
    def _handle_ambiguity(
        self,
        candidates: List[ResolverCandidate],
        context: dict,
    ) -> List[ResolverCandidate]:
        """
        Handle case where multiple candidates exist without an index.
        
        Detects repeated structures and either:
        - Uses recorded index from context
        - Fails loudly with ambiguity error
        """
        # Check if we have a recorded index in context
        recorded_index = context.get("recorded_index")
        if recorded_index is not None:
            try:
                return self._resolve_by_sibling_index(candidates, int(recorded_index))
            except (TypeError, ValueError):
                pass
        
        # Check if candidates share a repeating parent
        if self._is_repeated_structure(candidates):
            # Mark all candidates as ambiguous
            for candidate in candidates:
                candidate.reasons.append("in_repeated_structure")
                candidate.reasons.append("index_required")
            
            # Don't select any - this signals ambiguity
            # Return all candidates so the router can report the issue
            return candidates
        
        # Not a repeated structure, but still ambiguous
        for candidate in candidates:
            candidate.reasons.append("multiple_matches")
        
        return candidates
    
    def _is_repeated_structure(
        self,
        candidates: List[ResolverCandidate],
    ) -> bool:
        """
        Detect if candidates are part of a repeated structure.
        
        Checks if candidates share a common parent or grandparent
        that indicates repetition.
        """
        if len(candidates) < 2:
            return False
        
        # Check if all candidates have the same parent
        parent_ids = set()
        for candidate in candidates:
            if candidate.element.parent_id:
                parent_ids.add(candidate.element.parent_id)
        
        # Same direct parent
        if len(parent_ids) == 1:
            parent_id = list(parent_ids)[0]
            parent = self.dom_lookup.get(parent_id)
            
            if parent:
                if parent.tag.lower() in CONTAINER_TAGS:
                    return True
                if parent.role and parent.role.lower() in REPEATING_ROLES:
                    return True
            
            # Even without a known container tag, multiple siblings under
            # the same parent with the same tag suggests repetition
            tags = set(c.element.tag.lower() for c in candidates)
            if len(tags) == 1:
                return True
        
        # Check for shared grandparent via ancestor chains
        # (e.g., <ul><li><div><button> pattern)
        if len(parent_ids) > 1:
            grandparent_sets = []
            for candidate in candidates:
                ancestors = candidate.element.ancestors
                if len(ancestors) >= 2:
                    # Use tag+id of the 2nd ancestor as grandparent key
                    gp = ancestors[1]
                    gp_key = f"{gp.get('tag', '')}#{gp.get('id', '')}"
                    grandparent_sets.append(gp_key)
                else:
                    grandparent_sets.append(None)
            
            if grandparent_sets and all(g == grandparent_sets[0] and g is not None for g in grandparent_sets):
                return True
        
        return False
    
    def get_sibling_index(
        self,
        element: DOMElement,
        siblings: List[DOMElement],
    ) -> int:
        """
        Get the index of element among its siblings.
        
        Returns -1 if not found.
        """
        for i, sibling in enumerate(siblings):
            if sibling.node_id == element.node_id:
                return i
        return -1
