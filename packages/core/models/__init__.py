"""
Axiome v1 Schema Models

Pydantic models for Flow JSON schema and state-aware recording.
"""

from .enums import ActionType, GeneralizationLevel, PreferredStrategy, FailureBehavior
from .element import BoundingBox, ElementSnapshot, ContextNode
from .context import (
    RecordedContext,
    Resolution,
    ExpectedOutcome,
    Precondition,
    DOMExistenceCheck,
    StepStateMarkers,
)
from .flow import Selectors, Target, GeneralSettings, Step, ExtendedStep, Flow

# State-aware models
from .state import (
    PageIdentity,
    UIRegion,
    FormState,
    ModalState,
    AlertInfo,
    InteractionSummary,
    NavigationStructure,
    StateSnapshot,
)
from .graph import InteractionNode, GraphEdge, InteractionGraph
from .dom import DOMNode, DOMSnapshot, DOMNodeChange, TextChange, AttributeChange, DOMDiff
from .transition import ObservedChanges, StateTransition, SemanticPageLabels
from .config import RecorderConfig, DEFAULT_CONFIG

__all__ = [
    # Enums
    "ActionType",
    "GeneralizationLevel",
    "PreferredStrategy",
    "FailureBehavior",
    # Element models
    "BoundingBox",
    "ElementSnapshot",
    "ContextNode",
    # Context models
    "RecordedContext",
    "Resolution",
    "ExpectedOutcome",
    "Precondition",
    "DOMExistenceCheck",
    "StepStateMarkers",
    # Flow models
    "Selectors",
    "Target",
    "GeneralSettings",
    "Step",
    "ExtendedStep",
    "Flow",
    # State-aware models
    "PageIdentity",
    "UIRegion",
    "FormState",
    "ModalState",
    "AlertInfo",
    "InteractionSummary",
    "NavigationStructure",
    "StateSnapshot",
    "InteractionNode",
    "GraphEdge",
    "InteractionGraph",
    "DOMNode",
    "DOMSnapshot",
    "DOMNodeChange",
    "TextChange",
    "AttributeChange",
    "DOMDiff",
    "ObservedChanges",
    "StateTransition",
    "SemanticPageLabels",
    "RecorderConfig",
    "DEFAULT_CONFIG",
]
