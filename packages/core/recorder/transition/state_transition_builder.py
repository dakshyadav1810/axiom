"""
State Transition Builder for Axiome Recording Engine.

Creates state transition records linking user interactions
to observed UI state changes.
"""

from typing import Optional

from ..models import (
    StateSnapshot,
    StateTransition,
    DOMDiff,
)
from ..state import StateDiffEngine


class StateTransitionBuilder:
    """
    Builds state transition records.
    
    Links:
    - Trigger step (the user interaction)
    - Before state snapshot
    - After state snapshot
    - Observed changes (computed diff)
    - Optional DOM diff ID
    """
    
    def __init__(self):
        """Initialize with a state diff engine."""
        self._diff_engine = StateDiffEngine()
    
    def build(
        self,
        trigger_step_id: str,
        before_state: StateSnapshot,
        after_state: StateSnapshot,
        dom_diff: Optional[DOMDiff] = None
    ) -> StateTransition:
        """
        Build a state transition record.
        
        Args:
            trigger_step_id: ID of the step that caused the transition
            before_state: State snapshot before interaction
            after_state: State snapshot after interaction
            dom_diff: Optional DOM diff for additional tracking
            
        Returns:
            StateTransition with computed changes
        """
        # Compute observed changes
        observed_changes = self._diff_engine.compute_diff(before_state, after_state)
        
        return StateTransition(
            trigger_step_id=trigger_step_id,
            before_state_id=before_state.state_id,
            after_state_id=after_state.state_id,
            observed_changes=observed_changes,
            dom_diff_id=dom_diff.diff_id if dom_diff else None
        )
