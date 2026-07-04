"""
Flow-related Pydantic models for Axiome Recording Engine.

Contains the core Flow, Step, Target, and Selectors models
that define the complete structure of recorded test flows.
"""

from datetime import datetime, timezone
from typing import Any, Optional, TYPE_CHECKING
import uuid

from pydantic import BaseModel, Field

from .element import ElementSnapshot, ContextNode
from .context import (
    RecordedContext,
    Resolution,
    ExpectedOutcome,
    Precondition,
    StepStateMarkers,
    SelectionRule,
)
from .enums import ActionType, GeneralizationLevel, FailureBehavior

# Forward references for state-aware models
if TYPE_CHECKING:
    from .state import StateSnapshot
    from .graph import InteractionGraph
    from .dom import DOMSnapshot, DOMDiff
    from .transition import StateTransition, SemanticPageLabels


class Selectors(BaseModel):
    """
    Multiple selector strategies for element identification.
    
    Provides redundant ways to locate an element, enabling
    fallback strategies during test replay.
    
    Attributes:
        css: CSS selector
        xpath: XPath expression
        text: Text-based selector
        accessibility: Accessibility-based selector
        test_id: data-testid or similar attribute
    """
    css: Optional[str] = Field(None, description="CSS selector")
    xpath: Optional[str] = Field(None, description="XPath expression")
    text: Optional[str] = Field(None, description="Text-based selector")
    accessibility: Optional[str] = Field(
        None, 
        description="Accessibility selector (role + name)"
    )
    test_id: Optional[str] = Field(
        None, 
        description="Test ID attribute value"
    )


class Target(BaseModel):
    """
    Complete description of the interaction target element.
    
    Combines a friendly name, comprehensive element snapshot,
    multiple selector strategies, and semantic context path
    for robust element resolution.
    
    Attributes:
        friendly_name: Human-readable element identifier
        element_snapshot: Full element metadata at interaction time
        selectors: Multiple selector strategies
        context_path: Ancestry chain of semantic containers
        role: ARIA role (computed)
        label: Visible label text
        semantic_text: List of meaningful text associated with element
        attributes: Key semantic attributes
        index: Sibling index among same type/role
    """
    friendly_name: str = Field(..., description="Human-readable name")
    element_snapshot: ElementSnapshot = Field(
        ..., 
        description="Element metadata snapshot"
    )
    selectors: Selectors = Field(
        default_factory=Selectors,
        description="Selector strategies"
    )
    context_path: list[ContextNode] = Field(
        default_factory=list,
        description="Semantic ancestor chain"
    )
    role: Optional[str] = Field(None, description="Computed ARIA role")
    label: Optional[str] = Field(None, description="Associated label text")
    semantic_text: list[str] = Field(
        default_factory=list, 
        description="Meaningful text (visible, ancestor, etc.)"
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Key semantic attributes"
    )
    index: Optional[int] = Field(None, description="Sibling index")
    disambiguators: dict[str, Any] = Field(
        default_factory=dict,
        description="Compact disambiguation hints (row identity, hashes, etc.)",
    )
    action_intent: Optional[str] = Field(
        None,
        description="Inferred action intent hint (delete/edit/checkout/etc.)",
    )


class GeneralSettings(BaseModel):
    """
    Flow-level configuration settings.
    
    Attributes:
        default_generalization_level: Default matching strictness
        environment: Target environment name
    """
    default_generalization_level: GeneralizationLevel = Field(
        GeneralizationLevel.MODERATE,
        description="Default element matching strictness"
    )
    environment: Optional[str] = Field(
        None, 
        description="Target environment"
    )


class Step(BaseModel):
    """
    Single recorded user interaction step.
    
    Represents one atomic user action with full context
    for deterministic replay.
    
    Attributes:
        step_id: Unique identifier for this step
        order: Sequential order in the flow (1-indexed)
        action: Type of interaction performed
        target: Target element details (None for navigate)
        input_value: Input text for type/select actions
        resolution: Resolution preferences
        preconditions: Required conditions before execution
        expected_outcome: Expected result after execution
        failure_behavior: What to do if step fails
        recorded_context: Page state at interaction time
    """
    step_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique step identifier"
    )
    order: int = Field(..., ge=1, description="Step order (1-indexed)")
    action: ActionType = Field(..., description="Interaction type")
    target: Optional[Target] = Field(
        None, 
        description="Target element (None for navigate)"
    )
    input_value: Optional[str] = Field(
        None, 
        description="Input value for type/select"
    )
    resolution: Resolution = Field(
        default_factory=Resolution,
        description="Resolution preferences"
    )
    preconditions: list[Precondition] = Field(
        default_factory=list,
        description="Pre-execution conditions"
    )
    expected_outcome: Optional[ExpectedOutcome] = Field(
        None, 
        description="Expected result"
    )
    failure_behavior: Optional[FailureBehavior] = Field(
        None,
        description="Failure handling strategy (None = use hint-driven default)"
    )
    recorded_context: RecordedContext = Field(
        ..., 
        description="Page context at interaction"
    )
    test_data: list[str] = Field(
        default_factory=list,
        description="Data-driven test values"
    )
    state_markers: Optional[StepStateMarkers] = Field(
        None,
        description="Compact pre/post state markers around the interaction",
    )
    step_hints: Optional[dict] = Field(
        None,
        description="Auto-inferred hints (is_critical, suggested_outcome, etc.)",
    )
    selection_rule: Optional[SelectionRule] = Field(
        None,
        description="Group-selection strategy for repeating elements (product grids, etc.)",
    )


# Import state-aware models for ExtendedStep
from .state import StateSnapshot
from .graph import InteractionGraph
from .dom import DOMSnapshot, DOMDiff
from .transition import StateTransition, SemanticPageLabels


class ExtendedStep(Step):
    """
    Step with state-aware intelligence data attached.
    
    Extends the base Step with:
    - Before/after state snapshots
    - Interaction graph
    - State transition log
    - DOM snapshots and diff
    - Semantic page labels
    """
    before_state_snapshot: Optional[StateSnapshot] = Field(
        None, description="Page state before interaction"
    )
    after_state_snapshot: Optional[StateSnapshot] = Field(
        None, description="Page state after interaction"
    )
    interaction_graph: Optional[InteractionGraph] = Field(
        None, description="Interactive elements graph (after state)"
    )
    transition_log: Optional[StateTransition] = Field(
        None, description="State transition record"
    )
    dom_snapshot_before: Optional[DOMSnapshot] = Field(
        None, description="DOM tree before interaction"
    )
    dom_snapshot_after: Optional[DOMSnapshot] = Field(
        None, description="DOM tree after interaction"
    )
    dom_diff: Optional[DOMDiff] = Field(
        None, description="DOM structural changes"
    )
    semantic_page_labels: Optional[SemanticPageLabels] = Field(
        None, description="Rule-based page classification"
    )


class Flow(BaseModel):
    """
    Complete recorded test flow.
    
    Represents a full user journey through an application,
    consisting of multiple sequential steps.
    
    Attributes:
        flow_id: Unique identifier for this flow
        project_id: Parent project identifier
        flow_name: Human-readable flow name
        created_at: Flow creation timestamp
        base_url: Starting URL for the flow
        general_settings: Flow-level settings
        steps: Ordered list of interaction steps
    """
    flow_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique flow identifier"
    )
    project_id: str = Field(..., description="Project identifier")
    flow_name: str = Field(..., description="Flow name")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    base_url: str = Field(..., description="Starting URL")
    general_settings: GeneralSettings = Field(
        default_factory=GeneralSettings,
        description="Flow settings"
    )
    steps: list[Step] = Field(
        default_factory=list,
        description="Ordered interaction steps"
    )
    
    def add_step(self, step: Step) -> None:
        """
        Add a step to the flow.
        
        Automatically sets the step order based on current step count.
        
        Args:
            step: Step to add
        """
        step.order = len(self.steps) + 1
        self.steps.append(step)
    
    def to_json(self, indent: int = 2) -> str:
        """
        Serialize flow to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string representation
        """
        return self.model_dump_json(indent=indent)
