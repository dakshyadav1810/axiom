"""
Enumeration types for Axiome Recording Engine.

Defines the valid values for action types, generalization levels,
resolution strategies, and failure behaviors.
"""

from enum import Enum


class ActionType(str, Enum):
    """
    Types of user interactions that can be recorded.
    
    Attributes:
        NAVIGATE: Page navigation (URL change)
        CLICK: Mouse click on an element
        TYPE: Keyboard input into a field
        SELECT: Selection from dropdown/option list
        SUBMIT: Form submission
    """
    NAVIGATE = "navigate"
    CLICK = "click"
    HOVER = "hover"
    TYPE = "type"
    SELECT = "select"
    SUBMIT = "submit"
    WAIT = "wait"
    KEYPRESS = "keypress"
    SWITCH_CONTEXT = "switch_context"


class GeneralizationLevel(str, Enum):
    """
    How strictly to match elements during test replay.
    
    Attributes:
        MINIMAL: Exact match required (strictest)
        MODERATE: Allow minor variations
        FLEXIBLE: Semantic matching allowed (most lenient)
    """
    MINIMAL = "minimal"
    MODERATE = "moderate"
    FLEXIBLE = "flexible"


class PreferredStrategy(str, Enum):
    """
    Resolution strategy preference for element matching.
    
    Attributes:
        SAME_ELEMENT: Match the exact same element
        SEMANTIC_CONTEXT: Match by semantic meaning and context
        ANY_MATCHING: Accept any element matching criteria
        DIRECT_NAVIGATION: Navigate directly to target
    """
    SAME_ELEMENT = "same_element"
    SEMANTIC_CONTEXT = "semantic_context"
    ANY_MATCHING = "any_matching"
    DIRECT_NAVIGATION = "direct_navigation"


class FailureBehavior(str, Enum):
    """
    What to do when a step fails during test execution.
    
    Attributes:
        STOP_TEST: Halt test execution on failure
        CONTINUE: Continue with remaining steps
        RETRY_ONCE: Retry the step once before failing
    """
    STOP_TEST = "stop_test"
    CONTINUE = "continue"
    RETRY_ONCE = "retry_once"
