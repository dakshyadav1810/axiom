"""
Context Resolver - Ensures element is in the correct UI region.

This resolver answers: "Is this element in the right place?"

Signals used:
- Shared form container
- Same modal/dialog ancestor
- Same card/section
- Route/page context

Scoring:
- Inside form: +0.4
- Inside modal: +0.5
- Same section: +0.2
"""
from typing import Optional, Dict, Union, List, Tuple

from .base import BaseResolver
from ..models.resolver_models import DOMElement, ResolverCandidate, ActionNode


# Maximum ancestor traversal depth to avoid overfitting
MAX_ANCESTOR_DEPTH = 5

# Context-relevant tags and roles
FORM_TAGS = {"form"}
MODAL_ROLES = {"dialog", "alertdialog", "modal"}
SECTION_TAGS = {"section", "article", "aside", "main", "nav", "header", "footer"}
CONTAINER_ATTRS = {"data-section", "data-region", "data-container"}


class ContextResolver(BaseResolver):
    """
    Context resolver ensures elements are in the expected UI region.
    
    This prevents matching semantically similar elements that are
    in different parts of the page (e.g., multiple "Submit" buttons).
    """
    
    name = "context"
    
    def __init__(self, dom_lookup: Optional[Dict[str, DOMElement]] = None):
        """
        Initialize with optional DOM lookup for ancestor traversal.
        
        Args:
            dom_lookup: Dict mapping node_id to DOMElement for tree traversal
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
        Score candidates based on their contextual position.
        
        Candidates in forms, modals, or specific sections get boosted.
        
        Args:
            candidates: Either DOMElements or existing ResolverCandidates
            action: The action being resolved
            context: Contains previous_elements, current_url, etc.
        """
        results = []
        
        for candidate in candidates:
            # Handle both DOMElement and ResolverCandidate inputs
            if isinstance(candidate, ResolverCandidate):
                resolver_candidate = candidate
                element = candidate.element
            else:
                resolver_candidate = ResolverCandidate(
                    element=candidate,
                    score=0.0,
                    reasons=[],
                )
                element = candidate
            
            # Score based on ancestors
            context_score, reasons = self._score_context(element, context, action)
            
            # Add to existing score and reasons
            resolver_candidate.context_score = context_score
            resolver_candidate.score += context_score
            resolver_candidate.reasons.extend(reasons)
            
            results.append(resolver_candidate)
        
        return self.rank_candidates(results)
    
    def _score_context(
        self,
        element: DOMElement,
        context: dict,
        action: ActionNode,
    ) -> Tuple[float, List[str]]:
        """
        Calculate context score by traversing ancestors.
        Normalized to 0-1 range.
        
        Returns (score, list of reasons).
        """
        score = 0.0
        reasons = []
        
        # Get ancestor chain
        ancestors = self._get_ancestors(element)
        
        # Track which bonuses we've already awarded to avoid double-counting
        awarded_form = False
        awarded_modal = False
        awarded_section = False
        awarded_container_attr = False
        context_path_score = 0.0
        
        # Check for context-relevant ancestors
        for ancestor in ancestors:
            tag = ancestor.get("tag", "").lower()
            role = (ancestor.get("role") or "").lower()
            attributes = ancestor.get("attributes", {})
            
            # Match against recorded context path — take best match only
            if action.target and action.target.context_path:
                for item in action.target.context_path:
                    item_score = 0.0
                    if isinstance(item, str):
                        if tag == item.lower():
                            item_score = 0.5
                    elif isinstance(item, dict):
                        recorded_tag = item.get("tag", "").lower()
                        recorded_role = (item.get("role") or "").lower()
                        recorded_class = item.get("class_name") or ""
                        
                        if recorded_tag and tag == recorded_tag:
                            item_score = max(item_score, 0.3)
                        if recorded_role and role == recorded_role:
                            item_score = max(item_score, 0.2)
                        if recorded_class:
                            ancestor_class = attributes.get("class", "")
                            if ancestor_class and recorded_class in ancestor_class:
                                item_score = max(item_score, 0.15)
                    
                    if item_score > 0:
                        context_path_score = max(context_path_score, item_score)
                        if item_score >= 0.3:
                            reason_str = f"context_path_match:'{tag}'"
                            if reason_str not in reasons:
                                reasons.append(reason_str)

            # Form context (award once)
            if not awarded_form and tag in FORM_TAGS:
                awarded_form = True
                reasons.append("inside_form")
            
            # Modal/dialog context (award once, don't double-count role+tag)
            if not awarded_modal and (role in MODAL_ROLES or tag == "dialog"):
                awarded_modal = True
                reasons.append("inside_modal")
            
            # Named section via data attributes (award once)
            if not awarded_container_attr:
                for attr in CONTAINER_ATTRS:
                    if attributes.get(attr):
                        awarded_container_attr = True
                        reasons.append(f"in_section:{attributes[attr]}")
                        break
            
            # Section tags (award once)
            if not awarded_section and tag in SECTION_TAGS:
                awarded_section = True
                reasons.append(f"in_{tag}")
        
        # Compute context score from individual signals (max, not sum)
        structural_score = 0.0
        if awarded_modal:
            structural_score = max(structural_score, 0.4)
        if awarded_form:
            structural_score = max(structural_score, 0.3)
        if awarded_container_attr:
            structural_score = max(structural_score, 0.2)
        if awarded_section:
            structural_score = max(structural_score, 0.1)
        
        # Combine path match + structural context
        score = min(1.0, context_path_score + structural_score)
        
        # --- Nearby text matching ---
        # For repeated identical elements (e.g. delete buttons in a table),
        # compare text from the nearest row/card container.  The recorded
        # nearby_text captures the product name / row content that uniquely
        # identifies which instance was clicked.
        recorded_nearby = None
        if action.target and action.target.element_snapshot:
            recorded_nearby = getattr(action.target.element_snapshot, "nearby_text", None)
        
        if recorded_nearby and element.nearby_text:
            nearby_sim = self._text_similarity(recorded_nearby, element.nearby_text)
            if nearby_sim > 0.3:
                nearby_bonus = min(0.5, nearby_sim * 0.6)
                score = min(1.0, score + nearby_bonus)
                reasons.append(f"nearby_text_match:{nearby_sim:.2f}")
            elif nearby_sim < 0.1 and recorded_nearby.strip():
                # Penalize: this is clearly a different row
                score = max(0.0, score - 0.15)
                reasons.append("nearby_text_mismatch")
        
        # Check URL context if provided
        expected_url = context.get("expected_url_contains")
        current_url = context.get("current_url", "")
        if expected_url and expected_url in current_url:
            score = min(1.0, score + 0.1)
            reasons.append("correct_route")
        
        return score, reasons
    
    def _get_ancestors(self, element: DOMElement) -> List[dict]:
        """
        Get ancestor chain.
        """
        if element.ancestors:
            return element.ancestors
            
        # Fallback to DOM traversal if needed (legacy)
        ancestors = []
        current = element
        depth = 0
        
        while current.parent_id and depth < MAX_ANCESTOR_DEPTH:
            parent = self.dom_lookup.get(current.parent_id)
            if not parent:
                break
            # Convert parent DOMElement to dict structure
            ancestors.append({
                "tag": parent.tag,
                "role": parent.role,
                "attributes": parent.attributes
            })
            current = parent
            depth += 1
        
        return ancestors

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """
        Compute word-overlap (Jaccard) similarity between two text strings.
        
        Returns a value 0.0 – 1.0 indicating how many words are shared.
        Case-insensitive and ignores punctuation.
        """
        import re
        def _tokenize(s: str) -> set:
            return set(re.sub(r"[^\w\s]", "", s.lower()).split())
        
        words_a = _tokenize(a)
        words_b = _tokenize(b)
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0
