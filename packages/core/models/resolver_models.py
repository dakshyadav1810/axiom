"""
Core data models for the deterministic testing engine.

These models define the structure of DOM elements, resolver candidates,
and action nodes used throughout the resolution pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


_GENERIC_SEMANTIC_TOKENS = {
    "a", "button", "link", "input", "select", "textarea",
    "div", "span", "img", "svg", "icon", "element",
}


def _is_weak_semantic_token(value: Optional[str]) -> bool:
    """Return True when text is too generic to steer semantic matching."""
    if not value:
        return True
    normalized = " ".join(str(value).strip().lower().split())
    if not normalized:
        return True
    if normalized in _GENERIC_SEMANTIC_TOKENS:
        return True
    if len(normalized) <= 1:
        return True
    return False


def _sanitize_semantic_text(values: Optional[list[str]]) -> list[str]:
    """Drop generic/noisy semantic tokens and dedupe while preserving order."""
    if not values:
        return []
    cleaned: list[str] = []
    for item in values:
        if _is_weak_semantic_token(item):
            continue
        text = str(item).strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


class ActionType(Enum):
    """Supported action types"""
    NAVIGATE = "navigate"
    CLICK = "click"
    HOVER = "hover"
    TYPE = "type"
    SELECT = "select"
    SUBMIT = "submit"
    WAIT = "wait"
    KEYPRESS = "keypress"
    GO_BACK = "go_back"
    REFRESH = "refresh"
    WAIT_FOR_STABLE = "wait_for_stable"
    SWITCH_CONTEXT = "switch_context"


class OnFailure(Enum):
    """Failure handling strategies"""
    ABORT = "abort"
    CONTINUE = "continue"
    RETRY_ONCE = "retry_once"
    # Step is expected to possibly fail (e.g. second submit in double_submit mutation
    # where the app correctly disables the button).  A failure counts as a warning,
    # not a test failure, and the flow continues.
    OPTIONAL = "optional"


class GeneralizationLevel(Enum):
    """How strictly to match elements"""
    SAME_ELEMENT = "same_element"  # Must match exact element
    ANY_MATCHING = "any_matching"  # Any element matching criteria
    # Recorded flow format values
    MINIMAL = "minimal"  # Maps to same_element
    MODERATE = "moderate"  # Maps to any_matching
    AGGRESSIVE = "aggressive"  # More flexible matching
    FLEXIBLE = "flexible"  # Most lenient (from recorder)


class FailureReason(Enum):
    """Classified failure reasons - no generic 'unknown' allowed"""
    SEMANTIC_NO_MATCH = "semantic_no_match"  # Legacy alias — prefer LOW_CONFIDENCE
    LOW_CONFIDENCE = "low_confidence"
    SEMANTIC_AMBIGUITY = "semantic_ambiguity"
    SELECTOR_NO_MATCH = "selector_no_match"
    SELECTOR_AMBIGUITY = "selector_ambiguity"
    CONTEXT_CONFLICT = "context_conflict"
    NOT_INTERACTABLE = "not_interactable"
    STATE_BLOCKED = "state_blocked"
    VALIDATION_FAILED = "validation_failed"
    NAVIGATION_FAILED = "navigation_failed"
    TIMEOUT = "timeout"


@dataclass
class BoundingBox:
    """Element bounding box coordinates"""
    x: float
    y: float
    width: float
    height: float


@dataclass
class DOMElement:
    """
    Normalized DOM element wrapper.
    
    This is the common abstraction used by all resolvers.
    Created from Playwright element handles via the DOM extraction logic.
    """
    node_id: str
    tag: str
    text: str
    normalized_text: str  # lowercase, trimmed, punctuation removed
    role: Optional[str] = None
    aria_label: Optional[str] = None
    attributes: dict = field(default_factory=dict)
    is_visible: bool = True
    is_enabled: bool = True
    is_focusable: bool = False
    has_click_handler: bool = False
    bounding_box: Optional[BoundingBox] = None
    parent_id: Optional[str] = None
    ancestors: list[dict] = field(default_factory=list)
    matches_recorded_selector: bool = False
    sibling_index: int = -1       # Position among same-tag siblings under same parent
    sibling_count: int = 0        # Total same-tag siblings under same parent
    nearby_text: str = ""         # Text from nearest row/card/list-item container
    
    # Playwright locator for actual interaction
    _locator: Optional[object] = field(default=None, repr=False)


@dataclass
class ResolverCandidate:
    """
    A candidate element with resolution scores and reasoning.
    
    Each resolver adds to the score and appends reasons explaining
    why the candidate was boosted or penalized.
    """
    element: DOMElement
    score: float
    reasons: list[str] = field(default_factory=list)
    
    # Individual resolver scores for debugging/logging
    semantic_score: float = 0.0
    context_score: float = 0.0
    selector_score: float = 0.0
    affordance_passed: bool = False
    
    def add_reason(self, reason: str) -> None:
        """Add a resolution reason"""
        self.reasons.append(reason)
    
    def compute_final_score(self, weights: Optional[dict] = None) -> float:
        """
        Compute weighted final score.
        
        Weights are dynamic based on page characteristics:
        - Text-heavy pages: boost semantic
        - Icon-heavy pages: boost selector
        - Form context: boost context
        
        Default weights (if not provided):
            semantic: 0.4, context: 0.3, selector: 0.2, affordance: 0.1
        """
        if weights is None:
            weights = {
                "semantic": 0.4,
                "context": 0.3,
                "selector": 0.2,
                "affordance": 0.1,
            }
        
        affordance_value = 1.0 if self.affordance_passed else 0.0
        self.score = (
            self.semantic_score * weights.get("semantic", 0.4) +
            self.context_score * weights.get("context", 0.3) +
            self.selector_score * weights.get("selector", 0.2) +
            affordance_value * weights.get("affordance", 0.1)
        )
        return self.score


@dataclass
class ElementSnapshot:
    """
    Snapshot of element state at recording time.
    Used for matching during playback.
    """
    tag: Optional[str] = None
    text: Optional[str] = None
    normalized_text: Optional[str] = None
    role: Optional[str] = None
    aria_label: Optional[str] = None
    attributes: Optional[dict] = None
    bounding_box: Optional[dict] = None
    is_visible: bool = True
    is_enabled: bool = True
    nearby_text: Optional[str] = None  # Text from nearest row/card ancestor


@dataclass
class Selectors:
    """
    Recorded selectors for element location.
    """
    css: Optional[str] = None
    xpath: Optional[str] = None
    text: Optional[str] = None
    accessibility: Optional[str] = None
    test_id: Optional[str] = None


@dataclass
class ActionTarget:
    """
    Target specification for an action.
    
    Contains all the signals needed to resolve an element:
    - Semantic: label, semantic_text, role
    - Structural: test_id, attributes
    - Navigation: url
    - Recorded: element_snapshot, selectors (from recorded flows)
    """
    # For navigate actions
    url: Optional[str] = None
    
    # Semantic signals
    label: Optional[str] = None
    semantic_text: Optional[list[str]] = None  # e.g., ["login", "sign in"]
    role: Optional[str] = None  # button, textbox, link, etc.
    
    # Structural signals
    test_id: Optional[str] = None  # data-testid value
    attributes: Optional[dict] = None  # other stable attributes
    
    # Index for repeated elements
    index: Optional[int] = None
    
    # Recorded flow fields
    friendly_name: Optional[str] = None
    element_snapshot: Optional[ElementSnapshot] = None
    selectors: Optional[Selectors] = None
    context_path: Optional[list[str]] = None
    disambiguators: Optional[dict] = None
    action_intent: Optional[str] = None


@dataclass
class Preconditions:
    """
    Conditions that must be met before executing an action.
    """
    url_contains: Optional[str] = None
    element_visible: Optional[bool] = None
    element_enabled: Optional[bool] = None
    modal_visible: Optional[bool] = None


@dataclass
class SelectionRule:
    """
    Group-selection strategy for repeating elements.
    Controls which sibling to pick during replay when 'vary from group' is active.
    """
    enabled: bool = False
    strategy: str = "round_robin"   # round_robin | random | by_text | exclude_previous
    group_selector: Optional[str] = None
    text_filter: Optional[str] = None


@dataclass
class ActionNode:
    """
    A single action to execute in the flow.
    
    Each action consists of:
    - An ID for logging/tracking
    - A type (click, type, navigate, wait)
    - A target specification
    - Optional value (for type actions)
    - Generalization level
    - Preconditions
    - Expected outcome (for assertion after execution)
    - Failure handling strategy
    """
    id: str  # step_id (UUID string) for unambiguous trace correlation
    type: ActionType
    target: ActionTarget
    value: Optional[str] = None  # For type actions
    generalization: GeneralizationLevel = GeneralizationLevel.SAME_ELEMENT
    preconditions: Optional[Preconditions] = None
    expected_outcome: Optional[dict] = None  # {outcome_type, value}
    selection_rule: Optional[SelectionRule] = None
    on_failure: OnFailure = OnFailure.ABORT
    recorded_url: Optional[str] = None
    context_id: Optional[str] = None
    opener_context_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "ActionNode":
        """Create ActionNode from JSON dictionary. Supports both legacy and recorded flow formats."""
        # Detect format: recorded flows use 'action' and 'step_id', legacy uses 'type' and 'id'
        is_recorded_format = "action" in data or "step_id" in data
        
        if is_recorded_format:
            return cls._from_recorded_format(data)
        else:
            return cls._from_legacy_format(data)
    
    @classmethod
    def _from_recorded_format(cls, data: dict) -> "ActionNode":
        """Parse recorded flow step format."""
        target_data = data.get("target") or {}
        
        # Parse element_snapshot if present
        element_snapshot = None
        if snapshot_data := target_data.get("element_snapshot"):
            element_snapshot = ElementSnapshot(
                tag=snapshot_data.get("tag"),
                text=snapshot_data.get("text"),
                normalized_text=snapshot_data.get("normalized_text"),
                role=snapshot_data.get("role"),
                aria_label=snapshot_data.get("aria_label"),
                attributes=snapshot_data.get("attributes"),
                bounding_box=snapshot_data.get("bounding_box"),
                is_visible=snapshot_data.get("is_visible", True),
                is_enabled=snapshot_data.get("is_enabled", True),
                nearby_text=snapshot_data.get("nearby_text"),
            )
        
        # Parse selectors if present
        selectors = None
        if selectors_data := target_data.get("selectors"):
            selectors = Selectors(
                css=selectors_data.get("css"),
                xpath=selectors_data.get("xpath"),
                text=selectors_data.get("text"),
                accessibility=selectors_data.get("accessibility"),
                test_id=selectors_data.get("test_id"),
            )
        
        # Use the recorded semantic_text if available (it contains rich signals
        # like nearby labels, headings, etc.), falling back to friendly_name + snapshot text
        friendly_name = target_data.get("friendly_name")
        recorded_semantic = target_data.get("semantic_text")
        if recorded_semantic and isinstance(recorded_semantic, list) and len(recorded_semantic) > 0:
            semantic_text = _sanitize_semantic_text(list(recorded_semantic))
            # Ensure friendly_name is included if not already present
            if friendly_name and not _is_weak_semantic_token(friendly_name) and friendly_name not in semantic_text:
                semantic_text.insert(0, friendly_name)
        else:
            semantic_text = []
            if friendly_name and not _is_weak_semantic_token(friendly_name):
                semantic_text.append(friendly_name)
            if element_snapshot and element_snapshot.text:
                if (not _is_weak_semantic_token(element_snapshot.text) and
                        element_snapshot.text not in semantic_text):
                    semantic_text.append(element_snapshot.text)

        clean_label = None if _is_weak_semantic_token(friendly_name) else friendly_name
        recorded_index = target_data.get("index")
        if recorded_index is not None:
            try:
                recorded_index = int(recorded_index)
            except (TypeError, ValueError):
                recorded_index = None
        
        # For navigate actions the URL is the destination, not the source page.
        # If a dedicated nav_url key exists use it; otherwise fall back to
        # recorded_context.url which captures the page URL at interaction time
        # (acceptable only for explicit navigate-type steps where the recorder
        # sets recorded_context.url to the destination).
        nav_url = None
        if data.get("action") == "navigate":
            nav_url = (
                data.get("nav_url")
                or data.get("input_value")
                or data.get("recorded_context", {}).get("url")
            )

        # Build target with both legacy and recorded fields
        target = ActionTarget(
            url=nav_url,
            label=clean_label,
            semantic_text=semantic_text if semantic_text else None,
            role=element_snapshot.role if element_snapshot else None,
            test_id=selectors.test_id if selectors else None,
            attributes=element_snapshot.attributes if element_snapshot else None,
            index=recorded_index,
            friendly_name=friendly_name,
            element_snapshot=element_snapshot,
            selectors=selectors,
            context_path=target_data.get("context_path"),
            disambiguators=target_data.get("disambiguators"),
            action_intent=target_data.get("action_intent"),
        )
        
        # Parse preconditions (recorded format uses list of typed objects, convert to Preconditions)
        preconditions = None
        if pre_list := data.get("preconditions"):
            if isinstance(pre_list, dict):
                preconditions = Preconditions(
                    url_contains=pre_list.get("url_contains"),
                    element_visible=pre_list.get("element_visible"),
                    element_enabled=pre_list.get("element_enabled"),
                    modal_visible=pre_list.get("modal_visible"),
                )
            elif isinstance(pre_list, list) and pre_list:
                # Convert list of Precondition objects to flat Preconditions
                url_contains = None
                element_visible = None
                element_enabled = None
                modal_visible = None
                for p in pre_list:
                    if isinstance(p, dict):
                        ct = p.get("condition_type", "")
                        if ct == "url_contains":
                            url_contains = p.get("expected_value")
                        elif ct == "element_visible":
                            element_visible = True
                            # Use selector as a secondary signal if present
                        elif ct == "element_enabled":
                            element_enabled = True
                        elif ct == "modal_visible":
                            modal_visible = p.get("expected_value", True)
                if any(v is not None for v in [url_contains, element_visible, element_enabled, modal_visible]):
                    preconditions = Preconditions(
                        url_contains=url_contains,
                        element_visible=element_visible,
                        element_enabled=element_enabled,
                        modal_visible=modal_visible,
                    )
        
        # Parse action type — unknown types (scroll, drag, etc.) fall back to CLICK
        action_str = data.get("action", "click")
        try:
            action_type = ActionType(action_str)
        except ValueError:
            # Unrecognised action type: treat as CLICK so parsing doesn't abort the flow
            action_type = ActionType.CLICK
        
        # Parse generalization from resolution
        resolution = data.get("resolution", {})
        gen_level_str = resolution.get("generalization_level", "same_element")
        # Map recorded format values — preserve AGGRESSIVE/FLEXIBLE
        gen_map = {
            "minimal": "same_element",
            "moderate": "any_matching",
            "aggressive": "aggressive",
            "flexible": "flexible",
            "same_element": "same_element",
            "any_matching": "any_matching",
        }
        generalization = GeneralizationLevel(gen_map.get(gen_level_str, "same_element"))
        
        # Parse failure behavior
        # failure_behavior=None means "not explicitly set by user" — use hint-driven
        # default: abort only for steps that are explicitly stop_test, retry_once otherwise.
        failure_str = data.get("failure_behavior")
        failure_map = {
            "stop_test": "abort",
            "continue_test": "continue",
            "continue": "continue",
            "abort": "abort",
            "retry_once": "retry_once",
            "optional": "optional",
        }
        if failure_str is None:
            # Not explicitly set: derive from step hints
            hints = data.get("step_hints") or {}
            is_critical = hints.get("is_critical", False)
            on_failure = OnFailure.ABORT if is_critical else OnFailure.RETRY_ONCE
        else:
            on_failure = OnFailure(failure_map.get(str(failure_str), "retry_once"))
        
        # Parse selection_rule if present
        selection_rule = None
        if sr_data := data.get("selection_rule"):
            if isinstance(sr_data, dict) and sr_data.get("enabled"):
                selection_rule = SelectionRule(
                    enabled=True,
                    strategy=sr_data.get("strategy", "round_robin"),
                    group_selector=sr_data.get("group_selector"),
                    text_filter=sr_data.get("text_filter"),
                )

        # Parse expected_outcome if present
        expected_outcome = None
        if eo_data := data.get("expected_outcome"):
            if isinstance(eo_data, dict) and eo_data.get("outcome_type"):
                expected_outcome = {
                    "outcome_type": eo_data["outcome_type"],
                    "value": eo_data.get("value"),
                }

        # Use step_id as the action id for unambiguous trace correlation.
        # Fall back to order (int) coerced to str so the field type is always str.
        action_id = str(data.get("step_id") or data.get("order", 0))

        recorded_context = data.get("recorded_context", {}) if isinstance(data.get("recorded_context"), dict) else {}
        return cls(
            id=action_id,
            type=action_type,
            target=target,
            value=data.get("input_value"),
            generalization=generalization,
            preconditions=preconditions,
            expected_outcome=expected_outcome,
            selection_rule=selection_rule,
            on_failure=on_failure,
            recorded_url=recorded_context.get("url"),
            context_id=recorded_context.get("context_id"),
            opener_context_id=recorded_context.get("opener_context_id"),
        )
    
    @classmethod
    def _from_legacy_format(cls, data: dict) -> "ActionNode":
        """Parse legacy flow format."""
        target_data = data.get("target", {})
        target = ActionTarget(
            url=target_data.get("url"),
            label=target_data.get("label"),
            semantic_text=target_data.get("semantic_text"),
            role=target_data.get("role"),
            test_id=target_data.get("test_id") or target_data.get("data-testid"),
            attributes=target_data.get("attributes"),
            index=target_data.get("index"),
        )
        
        # Parse preconditions
        preconditions = None
        if pre_data := data.get("preconditions"):
            preconditions = Preconditions(
                url_contains=pre_data.get("url_contains"),
                element_visible=pre_data.get("element_visible"),
                element_enabled=pre_data.get("element_enabled"),
                modal_visible=pre_data.get("modal_visible"),
            )
        
        # Parse enums — unknown types fall back to CLICK to avoid crashing flow parse
        try:
            action_type = ActionType(data["type"])
        except (ValueError, KeyError):
            action_type = ActionType.CLICK
        generalization = GeneralizationLevel(
            data.get("generalization", "same_element")
        )
        on_failure = OnFailure(data.get("on_failure", "abort"))

        expected_outcome = None
        if eo_data := data.get("expected_outcome"):
            if isinstance(eo_data, dict) and eo_data.get("outcome_type"):
                expected_outcome = {
                    "outcome_type": eo_data["outcome_type"],
                    "value": eo_data.get("value"),
                }

        return cls(
            id=str(data["id"]),
            type=action_type,
            target=target,
            value=data.get("value"),
            generalization=generalization,
            preconditions=preconditions,
            expected_outcome=expected_outcome,
            on_failure=on_failure,
            recorded_url=data.get("recorded_url"),
            context_id=data.get("context_id"),
            opener_context_id=data.get("opener_context_id"),
        )


@dataclass
class FlowDefinition:
    """
    Complete flow definition loaded from JSON.
    """
    start_url: str
    actions: list[ActionNode]
    name: Optional[str] = None
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "FlowDefinition":
        """Create FlowDefinition from JSON dictionary. Supports both legacy and recorded flow formats."""
        # Detect format: recorded flows use 'steps' and 'flow_name', legacy uses 'actions' and 'name'
        is_recorded_format = "steps" in data or "flow_name" in data
        
        if is_recorded_format:
            # Recorded flow format
            steps = data.get("steps", [])
            actions = [ActionNode.from_dict(s) for s in steps]
            
            # Get start_url from base_url or first step's recorded_context
            start_url = data.get("base_url")
            if not start_url and steps:
                start_url = steps[0].get("recorded_context", {}).get("url", "")
            
            return cls(
                start_url=start_url or "",
                actions=actions,
                name=data.get("flow_name"),
                description=data.get("description"),
            )
        else:
            # Legacy format
            actions = [ActionNode.from_dict(a) for a in data.get("actions", [])]
            return cls(
                start_url=data["start_url"],
                actions=actions,
                name=data.get("name"),
                description=data.get("description"),
            )


@dataclass
class ResolutionResult:
    """
    Result of the resolver pipeline for a single action.
    """
    success: bool
    selected_element: Optional[DOMElement] = None
    selected_candidate: Optional[ResolverCandidate] = None
    all_candidates: list[ResolverCandidate] = field(default_factory=list)
    failure_reason: Optional[FailureReason] = None
    failure_message: Optional[str] = None
    resolver_path: list[str] = field(default_factory=list)  # e.g., ["semantic", "context", "affordance"]
    
    # Stats for logging
    semantic_candidates_count: int = 0
    context_filtered_count: int = 0
    affordance_passed_count: int = 0
    time_taken_ms: float = 0.0
    
    # Confidence policy metadata
    confidence_band: str = "low"  # high | medium | low
    confidence_warning: Optional[str] = None


@dataclass
class ActionResult:
    """
    Result of executing a single action.
    """
    action_id: str  # step_id (UUID string) for trace correlation
    success: bool
    resolution: Optional[ResolutionResult] = None
    failure_reason: Optional[FailureReason] = None
    failure_message: Optional[str] = None
    time_taken_ms: float = 0.0
    screenshot_path: Optional[str] = None
    selection_source: Optional[str] = None  # direct | resolver | none
    attempt_trace: list[dict] = field(default_factory=list)


@dataclass
class FlowResult:
    """
    Result of executing an entire flow.
    """
    success: bool
    actions_executed: int
    actions_passed: int
    actions_failed: int
    action_results: list[ActionResult] = field(default_factory=list)
    total_time_ms: float = 0.0
    failure_reason: Optional[FailureReason] = None
