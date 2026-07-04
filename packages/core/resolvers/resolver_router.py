from __future__ import annotations

"""
Resolver Router - Orchestrates the multi-resolver pipeline.

This module routes element resolution through the appropriate resolvers
based on page characteristics and action type.

Routing rules (Mixture of Experts):
- Modal or form detected → Semantic + Context
- High text density → Semantic + Context
- Icon-heavy UI → Selector + Affordance
- Repeated grid/list → Context + Index
- Default → Semantic + Context

Final Score Calculation:
    final = semantic * 0.4 + context * 0.3 + selector * 0.2 + affordance * 0.1
"""

import time
from typing import Optional, Dict, List, Union
from dataclasses import dataclass

from ..models.resolver_models import (
    DOMElement,
    ResolverCandidate,
    ActionNode,
    ActionType,
    ResolutionResult,
    FailureReason,
    GeneralizationLevel,
)
from . import (
    SemanticResolver,
    ContextResolver,
    SelectorResolver,
    AffordanceResolver,
    IndexResolver,
)


# ANSI color helpers (shared with executor.py)
class _C:
    DIM   = "\033[2m"
    RESET = "\033[0m"


# Confidence thresholds
CONFIDENCE_THRESHOLD = 0.5  # Minimum score to select an element
CONFIDENCE_MARGIN = 0.15    # Minimum margin over second-best candidate
HIGH_CONFIDENCE_THRESHOLD = 0.78
MEDIUM_CONFIDENCE_THRESHOLD = CONFIDENCE_THRESHOLD
HIGH_MARGIN_THRESHOLD = 0.20
MEDIUM_MARGIN_THRESHOLD = 0.08
WEAK_SEMANTIC_TOKENS = {
    "a", "button", "link", "input", "select", "textarea",
    "div", "span", "img", "svg", "icon", "element",
}


@dataclass
class PageCharacteristics:
    """Computed page features for routing decisions."""
    text_density: float = 0.0      # Ratio of text content to total elements
    icon_only_ratio: float = 0.0   # Ratio of icon-only elements
    interactive_count: int = 0      # Number of interactive elements
    has_modal: bool = False
    has_form: bool = False
    has_repeated_structure: bool = False


class ResolverRouter:
    """
    Routes element resolution through the appropriate resolver pipeline.
    
    This is the core orchestrator that:
    1. Characterizes the page
    2. Selects the appropriate resolution strategy
    3. Runs candidates through resolvers
    4. Applies weighted scoring
    5. Selects the best candidate or fails explicitly
    """
    
    def __init__(self):
        """Initialize all resolvers."""
        self.semantic = SemanticResolver()
        self.context = ContextResolver()
        self.selector = SelectorResolver()
        self.affordance = AffordanceResolver()
        self.index = IndexResolver()
        
        # DOM lookup for ancestor traversal
        self._dom_lookup: dict[str, DOMElement] = {}
    
    def set_dom_lookup(self, elements: list[DOMElement]) -> None:
        """
        Build DOM lookup table for ancestor traversal.
        
        Args:
            elements: All DOM elements on the page
        """
        self._dom_lookup = {el.node_id: el for el in elements}
        self.context.set_dom_lookup(self._dom_lookup)
        self.index.set_dom_lookup(self._dom_lookup)
    
    def resolve(
        self,
        candidates: list[DOMElement],
        action: ActionNode,
        context: dict,
        verbose: bool = True,
    ) -> ResolutionResult:
        """
        Resolve the target element for an action.
        
        This is the main entry point for element resolution.
        
        Args:
            candidates: All visible, enabled DOM elements on the page
            action: The action to resolve
            context: Additional context (URL, previous elements, etc.)
        
        Returns:
            ResolutionResult with selected element or failure reason
        """
        start_time = time.time()
        
        # Build DOM lookup if not already done
        if not self._dom_lookup:
            self.set_dom_lookup(candidates)
        
        # Characterize page for routing
        page_chars = self._characterize_page(candidates)
        
        # Select resolution strategy
        resolver_path = self._select_strategy(page_chars, action)
        
        # Log page characteristics (only when verbose)
        if verbose:
            traits = []
            if page_chars.has_modal:  traits.append("modal")
            if page_chars.has_form:   traits.append("form")
            if page_chars.has_repeated_structure: traits.append("repeated")
            if page_chars.text_density > 0.7:    traits.append(f"text-heavy({page_chars.text_density:.0%})")
            if page_chars.icon_only_ratio > 0.3: traits.append(f"icons({page_chars.icon_only_ratio:.0%})")
            traits_str = ", ".join(traits) if traits else "default"
            print(f"  Page: {page_chars.interactive_count} elements  [{traits_str}]")
            print(f"  Strategy: {' → '.join(resolver_path)}")
        
        # Run through resolvers with dynamic weights
        result = self._run_pipeline(
            candidates,
            action,
            context,
            resolver_path,
            page_chars,
            verbose=verbose,
        )
        
        # Record timing
        result.time_taken_ms = (time.time() - start_time) * 1000
        result.resolver_path = resolver_path
        
        return result
    
    def _characterize_page(
        self,
        candidates: list[DOMElement],
    ) -> PageCharacteristics:
        """
        Compute page characteristics for routing decisions.
        
        These are cheap heuristics computed from the candidate elements.
        """
        chars = PageCharacteristics()
        
        if not candidates:
            return chars
        
        chars.interactive_count = len(candidates)
        
        # Count text vs icon-only elements
        text_elements = 0
        icon_elements = 0
        
        for el in candidates:
            if el.text and len(el.text.strip()) > 2:
                text_elements += 1
            elif el.role in ("img", "image") or el.tag.lower() == "svg":
                icon_elements += 1
            elif not el.text and el.aria_label:
                icon_elements += 1
        
        total = text_elements + icon_elements
        if total > 0:
            chars.text_density = text_elements / total
            chars.icon_only_ratio = icon_elements / total
        
        # Check for modal/form presence
        for el in candidates:
            if el.role in ("dialog", "alertdialog", "modal"):
                chars.has_modal = True
            if el.tag.lower() == "form":
                chars.has_form = True
        
        # Check parents for modal/form
        for el in candidates:
            parent = self._dom_lookup.get(el.parent_id) if el.parent_id else None
            while parent:
                if parent.role in ("dialog", "alertdialog", "modal"):
                    chars.has_modal = True
                if parent.tag.lower() == "form":
                    chars.has_form = True
                parent = self._dom_lookup.get(parent.parent_id) if parent.parent_id else None
        
        # Detect repeated structures: multiple candidates sharing the same parent
        parent_groups: dict[str, int] = {}
        for el in candidates:
            if el.parent_id:
                parent_groups[el.parent_id] = parent_groups.get(el.parent_id, 0) + 1
        if any(count >= 3 for count in parent_groups.values()):
            chars.has_repeated_structure = True
        
        return chars
    
    def _select_strategy(
        self,
        page_chars: PageCharacteristics,
        action: ActionNode,
    ) -> list[str]:
        """
        Select resolution strategy based on page characteristics.
        
        Returns list of resolver names to use in order.
        """
        # Use index resolver only when we trust index as a real disambiguator.
        # Keep affordance before index so index only picks among interactable
        # candidates and cannot force a dead candidate.
        if self._is_index_signal_reliable(action, page_chars):
            return ["semantic", "context", "selector", "affordance", "index"]
        
        # Modal or form → prioritize semantic + context
        if page_chars.has_modal or page_chars.has_form:
            return ["semantic", "context", "selector", "affordance"]
        
        # High icon ratio → use selector more heavily
        if page_chars.icon_only_ratio > 0.5:
            return ["selector", "semantic", "affordance"]
        
        # Repeated structures alone are not enough to run index resolver.
        # Without an explicit trustworthy index, index should not prune.
        if page_chars.has_repeated_structure:
            return ["semantic", "context", "selector", "affordance"]
        
        # Default strategy: semantic-first
        return ["semantic", "context", "selector", "affordance"]

    def _is_index_signal_reliable(
        self,
        action: ActionNode,
        page_chars: PageCharacteristics,
    ) -> bool:
        """Return True only when recorded index is likely intentional."""
        target = action.target
        if not target or target.index is None:
            return False

        if page_chars and page_chars.has_repeated_structure:
            return True

        disambiguators = target.disambiguators or {}
        sibling_count = disambiguators.get("sibling_count")
        if isinstance(sibling_count, int) and sibling_count > 1:
            return True

        snapshot_attrs = {}
        if target.element_snapshot and target.element_snapshot.attributes:
            snapshot_attrs = target.element_snapshot.attributes
        recorded_sibling_count = snapshot_attrs.get("sibling_count")
        return isinstance(recorded_sibling_count, int) and recorded_sibling_count > 1
    
    def _run_pipeline(
        self,
        candidates: list[DOMElement],
        action: ActionNode,
        context: dict,
        resolver_path: list[str],
        page_chars: PageCharacteristics = None,
        verbose: bool = True,
    ) -> ResolutionResult:
        """
        Run candidates through the selected resolver pipeline.
        
        Each resolver scores/filters candidates progressively.
        Weights are dynamically adjusted based on page characteristics.
        """
        result = ResolutionResult(success=False)
        
        # Start with all candidates
        current_candidates: list[DOMElement] | list[ResolverCandidate] = candidates
        
        # Track stats
        result.semantic_candidates_count = 0
        result.context_filtered_count = 0
        result.affordance_passed_count = 0
        
        # Run through each resolver in order
        for resolver_name in resolver_path:
            if not current_candidates:
                break
            
            # Skip semantic resolver when the action target has no text
            # signals (icon buttons, SVG elements, image-only buttons).
            # Semantic scoring requires label/semantic_text to compare
            # against; without any, it would either pass-through all
            # candidates at score 0 or (historically) eliminate all of them.
            # Skipping it lets selector/context/affordance handle resolution.
            if resolver_name == "semantic":
                target = action.target
                has_semantic_signals = self._has_meaningful_semantic_signal(target.label, target.semantic_text)
                if not has_semantic_signals:
                    if verbose:
                        print(f"  ├─ {'semantic':<12}  {len(current_candidates)} → {len(current_candidates)}  (skipped: no text signals)")
                    continue
            
            before_count = len(current_candidates)
            
            if resolver_name == "semantic":
                current_candidates = self.semantic.resolve(
                    current_candidates, action, context
                )
                result.semantic_candidates_count = len(current_candidates)
                
            elif resolver_name == "context":
                current_candidates = self.context.resolve(
                    current_candidates, action, context
                )
                result.context_filtered_count = len(current_candidates)
                
            elif resolver_name == "selector":
                current_candidates = self.selector.resolve(
                    current_candidates, action, context
                )
                
            elif resolver_name == "affordance":
                current_candidates = self.affordance.resolve(
                    current_candidates, action, context
                )
                result.affordance_passed_count = len(current_candidates)
                
            elif resolver_name == "index":
                current_candidates = self.index.resolve(
                    current_candidates, action, context
                )
            
            after_count = len(current_candidates)
            if verbose:
                delta_str = f"{before_count} → {after_count}"
                if after_count < before_count:
                    delta_str += f"  (−{before_count - after_count})"
                print(f"  ├─ {resolver_name:<12}  {delta_str}")
        
        # Convert to list of ResolverCandidate
        if current_candidates and isinstance(current_candidates[0], DOMElement):
            current_candidates = [
                ResolverCandidate(element=el, score=0.0, reasons=[])
                for el in current_candidates
            ]
        
        # Compute dynamic weights based on page characteristics
        weights = self._compute_dynamic_weights(page_chars, action)
        
        # --- Post-hoc weight correction based on actual resolver output ---
        # If a resolver produced zero signal across ALL candidates, it has
        # no basis for scoring.  Zero its weight and redistribute so it
        # doesn't dilute resolvers that did produce signal.
        if current_candidates and isinstance(current_candidates[0], ResolverCandidate):
            best_semantic = max((c.semantic_score for c in current_candidates), default=0)
            best_selector = max((c.selector_score for c in current_candidates), default=0)
            best_context  = max((c.context_score  for c in current_candidates), default=0)
            
            if best_semantic == 0 and weights.get("semantic", 0) > 0:
                weights["semantic"] = 0.0
            if best_selector == 0 and weights.get("selector", 0) > 0:
                weights["selector"] = 0.0
            if best_context == 0 and weights.get("context", 0) > 0:
                weights["context"] = 0.0
            
            # Re-normalize to 1.0
            total_w = sum(weights.values())
            if total_w > 0:
                for key in weights:
                    weights[key] = weights[key] / total_w
        
        # Log dynamic weights
        if verbose:
            w_parts = [f"{k}={v:.2f}" for k, v in sorted(weights.items())]
            print(f"  {_C.DIM}Weights:{_C.RESET}  {', '.join(w_parts)}")
        
        # Compute final scores with dynamic weights
        for candidate in current_candidates:
            if isinstance(candidate, ResolverCandidate):
                candidate.compute_final_score(weights)
        
        # Sort by score
        current_candidates = sorted(
            current_candidates,
            key=lambda c: c.score if isinstance(c, ResolverCandidate) else 0,
            reverse=True,
        )
        
        result.all_candidates = current_candidates
        
        # Select best candidate
        return self._select_best(result, action, context)
    
    def _compute_dynamic_weights(
        self,
        page_chars: PageCharacteristics,
        action: ActionNode,
    ) -> dict:
        """
        Compute dynamic weights based on page characteristics and action target.
        
        Weighting strategy:
        - Icon-heavy UI (icon_only_ratio > 0.5): boost selector weight
        - Text-heavy UI (text_density > 0.7): boost semantic weight
        - Form context: boost context weight
        - Target has no semantic text: reduce semantic, boost selector
        """
        # Default weights
        weights = {
            "semantic": 0.4,
            "context": 0.3,
            "selector": 0.2,
            "affordance": 0.1,
        }
        
        if page_chars is None:
            return weights
        
        # Icon-heavy pages: semantic is less useful, boost selector
        if page_chars.icon_only_ratio > 0.5:
            weights["semantic"] = 0.2
            weights["selector"] = 0.4
            weights["context"] = 0.3
            weights["affordance"] = 0.1
        
        # Text-heavy pages: semantic is very useful
        elif page_chars.text_density > 0.7:
            weights["semantic"] = 0.5
            weights["context"] = 0.25
            weights["selector"] = 0.15
            weights["affordance"] = 0.1
        
        # Form context: context is more important
        if page_chars.has_form or page_chars.has_modal:
            # Boost context weight
            weights["context"] = min(0.4, weights["context"] + 0.1)
            # Reduce semantic slightly
            weights["semantic"] = max(0.2, weights["semantic"] - 0.05)
        
        # --- Per-target signal availability ---
        # Zero out weight for resolvers that have NO usable signal for
        # this specific target, then redistribute to those that do.
        # This prevents "empty voters" from diluting real signals.
        target = action.target
        
        has_semantic_signals = self._has_meaningful_semantic_signal(target.label, target.semantic_text)
        has_selector_signals = bool(
            target.test_id
            or (target.selectors and target.selectors.css)
            or (target.element_snapshot and target.element_snapshot.tag)
            or (target.attributes and any(v for v in target.attributes.values() if v))
        )
        
        if not has_semantic_signals:
            weights["semantic"] = 0.0
        if not has_selector_signals:
            weights["selector"] = 0.0
        
        # Normalize weights to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            for key in weights:
                weights[key] = weights[key] / total
        
        return weights

    @staticmethod
    def _is_meaningful_semantic_token(value: Optional[str]) -> bool:
        if not value:
            return False
        token = " ".join(str(value).strip().lower().split())
        if not token:
            return False
        if token in WEAK_SEMANTIC_TOKENS:
            return False
        if len(token) <= 1:
            return False
        return True

    def _has_meaningful_semantic_signal(
        self,
        label: Optional[str],
        semantic_text: Optional[list[str]],
    ) -> bool:
        if self._is_meaningful_semantic_token(label):
            return True
        if semantic_text and any(self._is_meaningful_semantic_token(t) for t in semantic_text):
            return True
        return False
    
    def _select_best(
        self,
        result: ResolutionResult,
        action: ActionNode,
        context: Optional[dict] = None,
    ) -> ResolutionResult:
        """
        Select the best candidate from scored results.
        
        Applies confidence threshold and margin requirements.
        Respects the action's generalization level:
        - SAME_ELEMENT / MINIMAL: strict margin required (fail on ambiguity)
        - ANY_MATCHING / MODERATE: accept best candidate even if ambiguous
        - AGGRESSIVE / FLEXIBLE: accept any match above threshold
        """
        candidates = result.all_candidates
        
        # No candidates → fail
        if not candidates:
            result.success = False
            result.failure_reason = FailureReason.LOW_CONFIDENCE
            result.failure_message = "No candidates found matching target criteria"
            return result
        
        best = candidates[0]
        context = context or {}

        # Phase-1 hard tiebreakers: only apply when top candidates are within the
        # confidence margin — prevents a low-score id/selector match from overriding
        # a clearly superior semantic candidate.
        margin_tight = len(candidates) < 2 or (candidates[0].score - candidates[1].score) < CONFIDENCE_MARGIN
        if margin_tight:
            hard_pref = self._pick_hard_anchor_candidate(candidates, action)
            if hard_pref is not None:
                best = hard_pref
                best.reasons.append("hard_tiebreaker:durable_anchor")

        # Guardrail: for non-navigation click targets (e.g., icon delete controls),
        # avoid selecting a link that would navigate away when a similarly scored
        # non-navigating candidate exists.
        if action.type == ActionType.CLICK:
            target_href = None
            if action.target and action.target.attributes:
                target_href = action.target.attributes.get("href")
            if not target_href and action.target and action.target.element_snapshot and action.target.element_snapshot.attributes:
                target_href = action.target.element_snapshot.attributes.get("href")
            best_href = best.element.attributes.get("href")
            if not target_href and best_href:
                near_ties = [c for c in candidates if (best.score - c.score) <= (CONFIDENCE_MARGIN + 0.05)]
                safer = [c for c in near_ties if not c.element.attributes.get("href")]
                if safer:
                    safer_sorted = sorted(safer, key=lambda c: c.score, reverse=True)
                    replacement = safer_sorted[0]
                    replacement.reasons.append("navigation_guard:prefer_non_href_candidate")
                    best = replacement
                else:
                    # If the action did not expect navigation but best is a link
                    # and alternatives are too close, fail safely instead of
                    # risking opening the wrong page.
                    if len(near_ties) > 1:
                        result.success = False
                        result.failure_reason = FailureReason.SEMANTIC_AMBIGUITY
                        result.failure_message = (
                            "Ambiguous click: only href-bearing candidates are near top "
                            "for a non-navigation target; failing safely"
                        )
                        result.confidence_band = "low"
                        return result
        
        # Check confidence threshold
        if best.score < CONFIDENCE_THRESHOLD:
            result.success = False
            result.failure_reason = FailureReason.LOW_CONFIDENCE
            result.failure_message = (
                f"Best candidate score {best.score:.2f} below threshold {CONFIDENCE_THRESHOLD}"
            )
            return result
        
        # Determine if strict margin check applies based on generalization level
        strict_generalization = action.generalization in (
            GeneralizationLevel.SAME_ELEMENT,
            GeneralizationLevel.MINIMAL,
        )
        
        # Check margin over second-best (if exists)
        if len(candidates) > 1:
            second = candidates[1]
            margin = best.score - second.score
            
            if margin < CONFIDENCE_MARGIN:
                # Tiebreaker: if one candidate matches the recorded CSS
                # selector, it is structurally the same element that was
                # recorded.  Use it to resolve ambiguity regardless of
                # generalization level.
                tied = [c for c in candidates if best.score - c.score < CONFIDENCE_MARGIN]
                selector_matches = [c for c in tied if c.element.matches_recorded_selector]
                
                if selector_matches:
                    best = selector_matches[0]
                    best.reasons.append(f"ambiguity_resolved:recorded_selector_from_{len(tied)}")
                else:
                    hard_tie_pick = self._pick_hard_anchor_candidate(tied, action)
                    if hard_tie_pick is not None:
                        best = hard_tie_pick
                        best.reasons.append(f"ambiguity_resolved:hard_anchor_from_{len(tied)}")
                        tied = [best] + [c for c in tied if c is not best]

                    # --- P2: Position & sibling tiebreaker ---
                    # If we have a recorded bounding box, pick the candidate
                    # closest to the recorded position (Euclidean distance to center).
                    position_resolved = False
                    recorded_bbox = None
                    if action.target and action.target.element_snapshot:
                        recorded_bbox = action.target.element_snapshot.bounding_box
                    
                    if recorded_bbox and isinstance(recorded_bbox, dict):
                        rec_cx = recorded_bbox.get("x", 0) + recorded_bbox.get("width", 0) / 2
                        rec_cy = recorded_bbox.get("y", 0) + recorded_bbox.get("height", 0) / 2
                        
                        def _bbox_dist(c):
                            bb = c.element.bounding_box
                            if not bb:
                                return float("inf")
                            cx = bb.x + bb.width / 2
                            cy = bb.y + bb.height / 2
                            return ((cx - rec_cx) ** 2 + (cy - rec_cy) ** 2) ** 0.5
                        
                        by_dist = sorted(tied, key=_bbox_dist)
                        closest = by_dist[0]
                        dist_val = _bbox_dist(closest)
                        # Only use if reasonably close (< 300px drift) and
                        # meaningfully closer than 2nd
                        if dist_val < 300 and (
                            len(by_dist) < 2 or _bbox_dist(by_dist[1]) - dist_val > 20
                        ):
                            best = closest
                            best.reasons.append(
                                f"ambiguity_resolved:bbox_proximity_{dist_val:.0f}px_from_{len(tied)}"
                            )
                            position_resolved = True
                    
                    # Sibling index tiebreaker: if the recorded element had a specific
                    # sibling_index, pick the candidate with the matching index
                    if not position_resolved and action.target and action.target.element_snapshot:
                        rec_attrs = action.target.element_snapshot.attributes or {}
                        # The sibling_index may be stored in the snapshot's extra data
                        # Also check the selectors object for sibling info
                        rec_sibling = rec_attrs.get("sibling_index")
                        if rec_sibling is not None:
                            try:
                                rec_idx = int(rec_sibling)
                                sibling_matches = [
                                    c for c in tied
                                    if c.element.sibling_index == rec_idx
                                ]
                                if len(sibling_matches) == 1:
                                    best = sibling_matches[0]
                                    best.reasons.append(
                                        f"ambiguity_resolved:sibling_index_{rec_idx}_from_{len(tied)}"
                                    )
                                    position_resolved = True
                            except (ValueError, TypeError):
                                pass
                    
                    # Nearby text tiebreaker: if the recorded element had
                    # nearby/container text (e.g. product row content),
                    # pick the candidate whose nearby text best matches.
                    if not position_resolved and action.target and action.target.element_snapshot:
                        rec_nearby = getattr(action.target.element_snapshot, "nearby_text", None)
                        if rec_nearby and rec_nearby.strip():
                            from .context import ContextResolver
                            sims = [
                                (c, ContextResolver._text_similarity(rec_nearby, c.element.nearby_text or ""))
                                for c in tied
                            ]
                            sims.sort(key=lambda x: x[1], reverse=True)
                            best_sim = sims[0][1]
                            if best_sim > 0.3 and (
                                len(sims) < 2 or sims[0][1] - sims[1][1] > 0.1
                            ):
                                best = sims[0][0]
                                best.reasons.append(
                                    f"ambiguity_resolved:nearby_text_{best_sim:.2f}_from_{len(tied)}"
                                )
                                position_resolved = True
                    
                    # --- Tag-preference tiebreaker ---
                    # When candidates are still tied after all positional/structural
                    # checks, prefer the ones whose tag matches the recorded snapshot
                    # tag.  Classic case: YouTube search results where a
                    # button[role=tab] "Videos" and several <a> video links all
                    # score identically — DOM-order would pick the tab button
                    # (higher up the page) instead of the first video link.
                    if not position_resolved and action.target and action.target.element_snapshot:
                        expected_tag = (action.target.element_snapshot.tag or "").strip().lower()
                        if expected_tag:
                            tag_matches = [
                                c for c in tied
                                if (c.element.tag or "").lower() == expected_tag
                            ]
                            if tag_matches and len(tag_matches) < len(tied):
                                # Narrow tied set; dom-order sort below will pick winner
                                tied = tag_matches
                                best.reasons.append(
                                    f"tiebreaker:tag_preference_{expected_tag}_narrowed_to_{len(tied)}"
                                )

                    if not position_resolved:
                        if strict_generalization:
                            # Strict mode: fail on ambiguity
                            result.success = False
                            result.failure_reason = FailureReason.SEMANTIC_AMBIGUITY
                            result.failure_message = (
                                f"Ambiguous: top two candidates too close "
                                f"({best.score:.2f} vs {second.score:.2f}, margin {margin:.2f})"
                            )
                            return result
                        elif action.generalization in (
                            GeneralizationLevel.AGGRESSIVE,
                            GeneralizationLevel.FLEXIBLE,
                            GeneralizationLevel.ANY_MATCHING,
                            GeneralizationLevel.MODERATE,
                        ):
                            # Deterministic: pick first by DOM order (lowest bounding box y, then x)
                            # from the (possibly tag-narrowed) tied set
                            tied_sorted = sorted(tied, key=lambda c: (
                                c.element.bounding_box.y if c.element.bounding_box else 0,
                                c.element.bounding_box.x if c.element.bounding_box else 0,
                            ))
                            best = tied_sorted[0]
                            best.reasons.append(f"ambiguity_resolved:dom_order_from_{len(tied)}")
                        else:
                            # ANY_MATCHING / MODERATE: pick first (stable, deterministic)
                            best = tied[0]
                            best.reasons.append(f"ambiguity_resolved:first_of_{len(tied)}")

        # Confidence-band policy (Phase-1):
        # - high: proceed
        # - medium: proceed with warning
        # - low: fail safely (no risky click)
        margin = None
        if len(candidates) > 1:
            margin = best.score - candidates[1].score
        band = self._classify_confidence(best.score, margin, best)
        result.confidence_band = band
        if band == "low":
            result.success = False
            result.failure_reason = FailureReason.LOW_CONFIDENCE
            margin_str = f"{margin:.2f}" if margin is not None else "n/a"
            result.failure_message = (
                f"Low confidence selection blocked (score={best.score:.2f}, margin={margin_str})"
            )
            return result
        if band == "medium":
            result.confidence_warning = (
                f"Medium confidence selection (score={best.score:.2f}"
                + (f", margin={margin:.2f})" if margin is not None else ")")
            )
        
        # Success!
        result.success = True
        result.selected_candidate = best
        result.selected_element = best.element
        
        return result

    def _pick_hard_anchor_candidate(
        self,
        candidates: list[ResolverCandidate],
        action: ActionNode,
    ) -> Optional[ResolverCandidate]:
        """Prefer candidate with strongest stable anchor match if unique."""
        if not candidates:
            return None

        target_attrs = action.target.attributes or {}
        snap_attrs = {}
        if action.target.element_snapshot and action.target.element_snapshot.attributes:
            snap_attrs = action.target.element_snapshot.attributes

        target_test_id = action.target.test_id or snap_attrs.get("data-testid") or target_attrs.get("data-testid")
        target_id = snap_attrs.get("id") or target_attrs.get("id")

        def _anchor_strength(c: ResolverCandidate) -> int:
            strength = 0
            attrs = c.element.attributes or {}
            if c.element.matches_recorded_selector:
                strength += 4
            if target_test_id:
                c_tid = attrs.get("data-testid") or attrs.get("data-test-id") or attrs.get("data-cy")
                if c_tid == target_test_id:
                    strength += 3
            if target_id and attrs.get("id") == target_id:
                strength += 2
            return strength

        ranked = sorted(candidates, key=lambda c: (_anchor_strength(c), c.score), reverse=True)
        if not ranked:
            return None
        best = ranked[0]
        best_strength = _anchor_strength(best)
        if best_strength <= 0:
            return None
        if len(ranked) == 1:
            return best
        second_strength = _anchor_strength(ranked[1])
        if best_strength > second_strength:
            return best
        return None

    def _classify_confidence(
        self,
        score: float,
        margin: Optional[float],
        candidate: ResolverCandidate,
    ) -> str:
        if score < MEDIUM_CONFIDENCE_THRESHOLD:
            return "low"
        if score >= HIGH_CONFIDENCE_THRESHOLD and (margin is None or margin >= HIGH_MARGIN_THRESHOLD):
            return "high"
        if margin is not None and margin < MEDIUM_MARGIN_THRESHOLD:
            # If we relied on weak fallback tie-breakers, downgrade to low.
            weak_reasons = (
                "ambiguity_resolved:first_of_",
                "ambiguity_resolved:dom_order_",
            )
            if any(any(r.startswith(w) for w in weak_reasons) for r in candidate.reasons):
                return "low"
            return "medium"
        return "medium"
    
    def describe_selection(self, result: ResolutionResult) -> str:
        """
        Generate a human-readable description of the resolution.
        
        Used for logging.
        """
        if not result.success:
            return f"FAILED: {result.failure_message}"
        
        candidate = result.selected_candidate
        element = result.selected_element
        
        # Build description
        desc_parts = []
        
        # Element identity
        if element.tag:
            desc_parts.append(element.tag)
        if element.role:
            desc_parts.append(f'role="{element.role}"')
        
        # Text content
        if element.text:
            text = element.text[:30] + "..." if len(element.text) > 30 else element.text
            desc_parts.append(f'"{text}"')
        elif element.aria_label:
            desc_parts.append(f'aria-label="{element.aria_label}"')
        
        # Score
        desc_parts.append(f"score={candidate.score:.2f}")
        
        return " ".join(desc_parts)
