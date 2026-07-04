from __future__ import annotations

"""
Selector Resolver - Structural fallback for low-text UIs.

This resolver answers: "Can we identify this element by what it is rather than what it says?"

Signals used:
- Role-based selectors
- Stable attributes (data-testid, id, name)
- Limited CSS selectors

This resolver is particularly useful for:
- Icon-only buttons
- SVG elements
- Low-text dashboard UIs
"""
from typing import Optional, Dict, List, Union, Tuple

from .base import BaseResolver
from ..models.resolver_models import DOMElement, ResolverCandidate, ActionNode


# Stable attributes that are reliable for matching
STABLE_ATTRS = [
    "data-testid",
    "data-test-id",
    "data-cy",
    "data-test",
    "id",
    "name",
    "type",
]

IMPLICIT_ROLE_BY_TAG = {
    "a": "link",
    "button": "button",
    "select": "combobox",
    "textarea": "textbox",
    "summary": "button",
}


class SelectorResolver(BaseResolver):
    """
    Selector resolver matches elements by structural identity.
    
    Never relies on brittle full CSS paths.
    Uses stable attributes and role-based matching.
    """
    
    name = "selector"
    
    def resolve(
        self,
        candidates: Union[List[DOMElement], List[ResolverCandidate]],
        action: ActionNode,
        context: dict,
    ) -> list[ResolverCandidate]:
        """
        Score candidates based on structural matching.
        
        Checks data-testid, role, and other stable attributes.
        """
        results = []
        
        # Get target selectors from action
        target_test_id = action.target.test_id
        target_role = action.target.role
        target_attrs = action.target.attributes or {}
        
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
            
            # Score based on selector matches
            selector_score, reasons = self._score_selectors(
                element,
                target_test_id,
                target_role,
                target_attrs,
                action,
            )
            
            # Add to existing score and reasons
            resolver_candidate.selector_score = selector_score
            resolver_candidate.score += selector_score
            resolver_candidate.reasons.extend(reasons)
            
            results.append(resolver_candidate)
        
        return self.rank_candidates(results)
    
    def _score_selectors(
        self,
        element: DOMElement,
        target_test_id: Optional[str],
        target_role: Optional[str],
        target_attrs: dict,
        action: ActionNode,
    ) -> Tuple[float, List[str]]:
        """
        Calculate selector score for an element.
        Normalized to 0-1 range.

        Returns (score, list of reasons).
        """
        score = 0.0
        reasons = []

        # 0. Recorded CSS/XPath match - capped to 1.0 (no longer 100)
        if element.matches_recorded_selector:
            score = max(score, 1.0)
            reasons.append("recorded_selector_match")

        # 1. data-testid match (most reliable)
        if target_test_id:
            element_test_id = (
                element.attributes.get("data-testid") or
                element.attributes.get("data-test-id") or
                element.attributes.get("data-cy") or
                element.attributes.get("data-test")
            )
            if element_test_id == target_test_id:
                score = max(score, 1.0)
                reasons.append(f"testid_match:'{target_test_id}'")

        # 2. Tag match
        target_snapshot = action.target.element_snapshot
        if target_snapshot and target_snapshot.tag and element.tag:
            if element.tag.lower() == target_snapshot.tag.lower():
                score = max(score, 0.3)
                reasons.append(f"tag_match:'{element.tag}'")
            else:
                # Negative signal: tag mismatch
                score -= 0.15
                reasons.append(f"tag_mismatch:{element.tag}!=expected:{target_snapshot.tag}")

        # 3. Role match with expanded synonyms and implicit-role parity
        ROLE_SYNONYMS = {
            ("input", "textbox"), ("textbox", "input"),
            ("a", "link"), ("link", "a"),
            ("button", "submit"), ("submit", "button"),
            ("combobox", "select"), ("select", "combobox"),
            ("listbox", "select"), ("select", "listbox"),
        }
        if target_role:
            el_role = self._effective_role(
                element.role,
                element.tag,
                element.attributes,
            )
            tgt_role = self._effective_role(
                target_role,
                target_snapshot.tag if target_snapshot else None,
                target_attrs,
            )
            if not tgt_role:
                tgt_role = str(target_role).lower()

            if el_role == tgt_role:
                score = max(score, 0.4)
                reasons.append(f"role_selector_match:'{target_role}'")
            elif (el_role, tgt_role) in ROLE_SYNONYMS:
                score = max(score, 0.35)
                reasons.append(f"role_synonym_match:'{target_role}'")
            else:
                # Negative signal: role mismatch
                score -= 0.1
                reasons.append(f"role_mismatch:{el_role}!=expected:{tgt_role}")

        # 4. Other stable attribute matches
        for attr, value in target_attrs.items():
            if attr in STABLE_ATTRS:
                element_value = element.attributes.get(attr)
                if element_value == value:
                    score += 0.15
                    reasons.append(f"attr_match:{attr}='{value}'")
            elif attr == "class" and value:
                element_class = element.attributes.get("class")
                if element_class == value:
                    score += 0.1
                    reasons.append("exact_class_match")
                elif element_class and value in element_class:
                    score += 0.05
                    reasons.append("partial_class_match")

        # 5. General attribute matching for all remaining snapshot attributes
        #    This naturally picks up href, src, action, method, for, etc.
        #    without needing a hardcoded whitelist.  These attributes are
        #    often highly discriminating (e.g. href="/trips" uniquely
        #    identifies a link among several with identical visible text).
        handled_attrs = set(STABLE_ATTRS) | {"class"}
        matched_general = 0
        compared_general = 0
        for attr, value in target_attrs.items():
            if attr in handled_attrs or not value:
                continue
            compared_general += 1
            element_value = element.attributes.get(attr)
            if element_value is not None and str(element_value) == str(value):
                matched_general += 1
                reasons.append(f"attr_match:{attr}")

        if compared_general > 0 and matched_general > 0:
            # Strong bonus — a single href match should be decisive
            attr_bonus = min(0.6, (matched_general / compared_general) * 0.6)
            score += attr_bonus
        elif compared_general > 0 and matched_general == 0:
            # Negative signal: target has attrs the live element doesn't share
            score -= 0.15
            reasons.append("attr_mismatch")

        # Cap to 0-1
        score = max(0.0, min(1.0, score))

        return score, reasons

    def _effective_role(
        self,
        explicit_role: Optional[str],
        tag: Optional[str],
        attrs: Optional[dict],
    ) -> Optional[str]:
        """Normalize explicit role and infer implicit role from tag/input type."""
        if explicit_role:
            return explicit_role.lower()
        if not tag:
            return None
        tag_l = str(tag).lower()
        if tag_l == "input":
            input_type = str((attrs or {}).get("type") or "text").lower()
            if input_type in {"submit", "button", "reset", "image"}:
                return "button"
            if input_type == "checkbox":
                return "checkbox"
            if input_type == "radio":
                return "radio"
            return "textbox"
        return IMPLICIT_ROLE_BY_TAG.get(tag_l)
    
    def find_by_test_id(
        self,
        candidates: List[DOMElement],
        test_id: str,
    ) -> List[DOMElement]:
        """
        Find elements matching a specific test ID.
        
        Useful for quick exact matches without full scoring.
        """
        results = []
        for element in candidates:
            element_test_id = (
                element.attributes.get("data-testid") or
                element.attributes.get("data-test-id") or
                element.attributes.get("data-cy") or
                element.attributes.get("data-test")
            )
            if element_test_id == test_id:
                results.append(element)
        return results
