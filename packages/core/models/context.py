"""
Context-related Pydantic models for Axiome Recording Engine.

Contains models for page context, resolution preferences,
preconditions, and expected outcomes.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .enums import GeneralizationLevel, PreferredStrategy


class RecordedContext(BaseModel):
    """
    Page context at the time of interaction.
    
    Captures environmental state that may be relevant
    for test reproducibility.
    
    Attributes:
        url: Full page URL at interaction time
        viewport_width: Browser viewport width in pixels
        viewport_height: Browser viewport height in pixels
        scroll_x: Horizontal scroll position
        scroll_y: Vertical scroll position
        timestamp: ISO 8601 timestamp of interaction
        page_title: Document title
    """
    url: str = Field(..., description="Page URL at interaction time")
    viewport_width: int = Field(..., gt=0, description="Viewport width")
    viewport_height: int = Field(..., gt=0, description="Viewport height")
    scroll_x: float = Field(0, description="Horizontal scroll position")
    scroll_y: float = Field(0, description="Vertical scroll position")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Interaction timestamp"
    )
    page_title: Optional[str] = Field(None, description="Document title")
    context_id: Optional[str] = Field(
        None,
        description="Recorded browser context/page identifier (ctx_N)",
    )
    opener_context_id: Optional[str] = Field(
        None,
        description="Recorded opener context identifier for popup/tab lineage",
    )


class Resolution(BaseModel):
    """
    Resolution preferences for element matching during replay.
    
    Configures how strictly to match elements and which
    strategy to prefer when multiple matches exist.
    
    Attributes:
        generalization_level: How strictly to match elements
        preferred_strategy: Which resolution approach to use
    """
    generalization_level: GeneralizationLevel = Field(
        GeneralizationLevel.MODERATE,
        description="Element matching strictness"
    )
    preferred_strategy: PreferredStrategy = Field(
        PreferredStrategy.SEMANTIC_CONTEXT,
        description="Resolution strategy preference"
    )


class ExpectedOutcome(BaseModel):
    """
    Expected result after step execution.
    
    Used during test replay to verify the step
    had the intended effect.
    
    Attributes:
        outcome_type: Type of expected outcome
        value: Expected value (optional)
        description: Human-readable description
    """
    outcome_type: str = Field(..., description="Type of expected outcome")
    value: Optional[Any] = Field(None, description="Expected value")
    description: Optional[str] = Field(
        None, 
        description="Human-readable outcome description"
    )


class Precondition(BaseModel):
    """
    Condition that must be true before step execution.
    
    Used during test replay to verify the page is in
    the expected state before proceeding.
    
    Attributes:
        condition_type: Type of precondition check
        selector: CSS selector for element check (optional)
        expected_value: Expected value to match
        description: Human-readable description
    """
    condition_type: str = Field(..., description="Type of precondition")
    selector: Optional[str] = Field(None, description="Element selector")
    expected_value: Optional[Any] = Field(None, description="Expected value")
    description: Optional[str] = Field(
        None, 
        description="Human-readable precondition description"
    )


class DOMExistenceCheck(BaseModel):
    """
    Lightweight selector existence snapshot for a single marker.
    """
    name: str = Field(..., description="Marker name")
    selector: str = Field(..., description="Selector used for check")
    exists: bool = Field(..., description="Whether selector matched any element")
    count: int = Field(..., ge=0, description="Matched element count")


class StepStateMarkers(BaseModel):
    """
    Compact pre/post state markers captured around step assembly.
    """
    pre_url: Optional[str] = Field(None, description="URL before post-check capture")
    post_url: Optional[str] = Field(None, description="URL after short settle delay")
    pre_checks: list[DOMExistenceCheck] = Field(
        default_factory=list,
        description="Selector existence checks captured before settle delay",
    )
    post_checks: list[DOMExistenceCheck] = Field(
        default_factory=list,
        description="Selector existence checks captured after settle delay",
    )
    transition_hint: Optional[str] = Field(
        None,
        description="Compact transition hint (url_changed/dom_changed/stable)",
    )


class SelectionRule(BaseModel):
    """
    Parameterised group-selection strategy for repeating elements
    (product grids, search results, data tables, etc.).

    Controls how the executor picks *which* sibling to interact with
    during replay variations.

    Attributes:
        enabled: Whether group selection is active for this step
        strategy: round_robin | random | by_text | exclude_previous
        group_selector: CSS selector identifying all siblings in the group
        text_filter: Optional text substring to prefer (strategy=by_text)
    """
    enabled: bool = Field(False, description="Activate group selection")
    strategy: str = Field(
        "round_robin",
        description="Selection strategy: round_robin | random | by_text | exclude_previous",
    )
    group_selector: Optional[str] = Field(
        None,
        description="CSS selector that matches all siblings in the group",
    )
    text_filter: Optional[str] = Field(
        None,
        description="Text substring filter (strategy=by_text)",
    )
