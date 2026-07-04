from __future__ import annotations

"""
Semantic Resolver - Primary resolver for meaning-based matching.

This resolver answers: "Does this element mean what the user intended?"

Signals used:
- Visible text (exact and partial match)
- Normalized text (lowercase, trimmed, punctuation removed)
- aria-label
- Role + accessible name pairing

Scoring:
- Exact visible text match: +1.0
- Partial visible text match: +0.6
- aria-label match: +0.9
- Role match: +0.2
"""

import re
import string
from typing import Optional

from rapidfuzz import fuzz

from .base import BaseResolver
from ..models.resolver_models import DOMElement, ResolverCandidate, ActionNode


# Minimum score to be considered a valid semantic match
# Semantic scoring is a SOFT scorer: every candidate gets a semantic_score
# attached but none are filtered out.  The final _select_best in
# resolver_router applies CONFIDENCE_THRESHOLD to decide acceptance.
SEMANTIC_MIN_SCORE = 0.3  # Kept for reference; no longer used as a hard filter

# Fuzzy match threshold (0-100 scale from rapidfuzz)
FUZZY_MATCH_THRESHOLD = 80

WEAK_SEMANTIC_TOKENS = {
    "a", "button", "link", "input", "select", "textarea",
    "div", "span", "img", "svg", "icon", "element",
}


def normalize_text(text: Optional[str]) -> str:
    """
    Normalize text for comparison.
    
    - Lowercase
    - Trim whitespace
    - Remove punctuation
    - Collapse multiple spaces
    """
    if not text:
        return ""
    
    # Lowercase
    result = text.lower()
    
    # Remove punctuation
    result = result.translate(str.maketrans("", "", string.punctuation))
    
    # Collapse whitespace
    result = re.sub(r"\s+", " ", result).strip()
    
    return result


class SemanticResolver(BaseResolver):
    """
    Primary resolver that matches elements by semantic meaning.
    
    This is the most important resolver for text-rich UIs.
    Uses both exact matching and fuzzy matching (via RapidFuzz).
    """
    
    name = "semantic"
    
    def resolve(
        self,
        candidates: list[DOMElement],
        action: ActionNode,
        context: dict,
    ) -> list[ResolverCandidate]:
        """
        Score candidates based on semantic similarity to target.
        
        Uses multiple signals:
        1. Visible text matching
        2. aria-label matching
        3. Role matching
        4. Semantic text keywords matching
        """
        results = []
        
        # Extract target signals from action
        target_label = action.target.label
        target_texts = action.target.semantic_text or []
        target_role = action.target.role
        
        # Normalize target for comparison
        normalized_label = normalize_text(target_label)
        normalized_targets = [normalize_text(t) for t in target_texts]
        
        # If we have a label, add it to targets
        if normalized_label:
            normalized_targets.insert(0, normalized_label)
        
        # Filter out empty/generic strings
        normalized_targets = [t for t in normalized_targets if self._is_meaningful_token(t)]
        
        # If we have NO semantic signals at all (icon-only buttons, SVG
        # elements, image buttons, etc.), pass through ALL candidates
        # unscored rather than filtering everyone to 0 and eliminating them.
        # Downstream resolvers (selector, affordance, context) can still
        # identify the right element via structural/positional matching.
        if not normalized_targets and not target_role:
            for element in candidates:
                candidate = ResolverCandidate(
                    element=element,
                    score=0.0,
                    reasons=["semantic_bypass:no_text_signals"],
                    semantic_score=0.0,
                )
                results.append(candidate)
            return self.rank_candidates(results)
        
        for element in candidates:
            score, reasons = self._score_element(
                element,
                normalized_targets,
                target_role,
            )
            
            # Semantic is a SCORER, not a filter.  Every candidate passes
            # through with its semantic_score attached.  Downstream
            # resolvers (context, selector, affordance) add their own
            # scores, and the final _select_best applies confidence
            # thresholds.  Only the affordance resolver acts as a hard
            # filter (removing non-actionable elements).
            candidate = ResolverCandidate(
                element=element,
                score=score,
                reasons=reasons,
                semantic_score=score,
            )
            results.append(candidate)
        
        return self.rank_candidates(results)

    @staticmethod
    def _is_meaningful_token(value: Optional[str]) -> bool:
        if not value:
            return False
        token = value.strip().lower()
        if not token:
            return False
        if token in WEAK_SEMANTIC_TOKENS:
            return False
        if len(token) <= 1:
            return False
        return True
    
    def _score_element(
        self,
        element: DOMElement,
        targets: list[str],
        target_role: Optional[str],
    ) -> tuple[float, list[str]]:
        """
        Calculate semantic score for a single element.
        
        Returns (score, list of reasons).
        Score is normalized to 0-1 range using max-of-signals approach.
        """
        reasons = []
        
        # Get element text sources
        element_text = element.normalized_text
        element_aria = normalize_text(element.aria_label)
        
        # Get additional semantic signals from attributes
        element_id = normalize_text(element.attributes.get("id", ""))
        element_name = normalize_text(element.attributes.get("name", ""))
        element_placeholder = normalize_text(element.attributes.get("placeholder", ""))
        
        # Track the best score from each signal channel independently.
        # We use max (not sum) across channels to keep scores in 0-1.
        text_score = 0.0
        aria_score = 0.0
        id_score = 0.0
        name_score = 0.0
        placeholder_score = 0.0
        role_score = 0.0
        
        # 1. Check visible text matches — check ALL targets, keep best
        for target in targets:
            if not target:
                continue
            s = 0.0
            reason = ""
            
            if element_text == target:
                s = 1.0
                reason = f"exact_text_match:'{target}'"
            elif len(target) >= 4 and target in element_text:
                # Require target >= 4 chars for substring match to avoid
                # false positives like "log" in "dialog"
                s = 0.6
                reason = f"partial_text_match:'{target}'"
            else:
                fuzzy = fuzz.ratio(element_text, target)
                if fuzzy >= FUZZY_MATCH_THRESHOLD:
                    s = (fuzzy / 100) * 0.5
                    reason = f"fuzzy_text_match:'{target}'({fuzzy}%)"
            
            if s > text_score:
                text_score = s
                if reason:
                    # Replace previous text reason
                    reasons = [r for r in reasons if not r.startswith(("exact_text", "partial_text", "fuzzy_text"))]
                    reasons.append(reason)
        
        # 2. Check aria-label matches — check ALL targets, keep best
        if element_aria:
            for target in targets:
                if not target:
                    continue
                s = 0.0
                reason = ""
                
                if element_aria == target:
                    s = 0.9
                    reason = f"aria_label_match:'{target}'"
                elif len(target) >= 4 and target in element_aria:
                    s = 0.5
                    reason = f"partial_aria_match:'{target}'"
                else:
                    fuzzy = fuzz.ratio(element_aria, target)
                    if fuzzy >= FUZZY_MATCH_THRESHOLD:
                        s = (fuzzy / 100) * 0.4
                        reason = f"fuzzy_aria_match:'{target}'({fuzzy}%)"
                
                if s > aria_score:
                    aria_score = s
                    if reason:
                        reasons = [r for r in reasons if not r.startswith(("aria_label", "partial_aria", "fuzzy_aria"))]
                        reasons.append(reason)
        
        # 3. Check id attribute matches
        if element_id:
            for target in targets:
                if not target:
                    continue
                if element_id == target:
                    if 0.85 > id_score:
                        id_score = 0.85
                        reasons.append(f"id_match:'{target}'")
                    break
                elif len(target) >= 4 and target in element_id:
                    if 0.5 > id_score:
                        id_score = 0.5
                        reasons.append(f"partial_id_match:'{target}'")
                    break
        
        # 4. Check name attribute matches
        if element_name:
            for target in targets:
                if not target:
                    continue
                if element_name == target:
                    if 0.8 > name_score:
                        name_score = 0.8
                        reasons.append(f"name_match:'{target}'")
                    break
                elif len(target) >= 4 and target in element_name:
                    if 0.45 > name_score:
                        name_score = 0.45
                        reasons.append(f"partial_name_match:'{target}'")
                    break
        
        # 5. Check placeholder matches
        if element_placeholder:
            for target in targets:
                if not target:
                    continue
                if element_placeholder == target:
                    if 0.7 > placeholder_score:
                        placeholder_score = 0.7
                        reasons.append(f"placeholder_match:'{target}'")
                    break
                elif len(target) >= 4 and target in element_placeholder:
                    if 0.4 > placeholder_score:
                        placeholder_score = 0.4
                        reasons.append(f"partial_placeholder_match:'{target}'")
                    break
        
        # 6. Check role match
        if target_role and element.role:
            if element.role.lower() == target_role.lower():
                role_score = 0.2
                reasons.append(f"role_match:'{target_role}'")
        
        # Combine: primary signal = max(text, aria, id, name, placeholder)
        # Secondary boost = role (always additive, small)
        # This keeps the total in roughly 0-1.2 range.
        primary = max(text_score, aria_score, id_score, name_score, placeholder_score)
        # Add a small bonus if multiple independent channels match
        secondary_hits = sum(1 for s in [text_score, aria_score, id_score, name_score, placeholder_score] if s > 0)
        multi_signal_bonus = min(0.15, (secondary_hits - 1) * 0.05) if secondary_hits > 1 else 0.0
        
        score = min(1.0, primary + multi_signal_bonus + role_score)
        
        return score, reasons
