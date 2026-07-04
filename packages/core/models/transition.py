"""
State Transition Models for Axiome Recording Engine.

Pydantic models for tracking cause/effect relationships
between user interactions and UI state changes.
"""

from datetime import datetime, timezone
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class ObservedChanges(BaseModel):
    """
    Detailed breakdown of observed UI changes between states.
    
    Provides deterministic diff results for analysis.
    """
    url_changed: bool = Field(False, description="URL changed")
    title_changed: bool = Field(False, description="Page title changed")
    
    new_regions: list[str] = Field(
        default_factory=list,
        description="IDs of newly added UI regions"
    )
    removed_regions: list[str] = Field(
        default_factory=list,
        description="IDs of removed UI regions"
    )
    
    modal_opened: bool = Field(False, description="Modal/dialog was opened")
    modal_closed: bool = Field(False, description="Modal/dialog was closed")
    
    form_validity_changed: bool = Field(
        False, description="Form validation state changed"
    )
    form_fields_changed: bool = Field(
        False, description="Form field values changed"
    )
    
    alerts_added: list[str] = Field(
        default_factory=list,
        description="New alert texts"
    )
    alerts_removed: list[str] = Field(
        default_factory=list,
        description="Removed alert texts"
    )
    
    interaction_count_delta: int = Field(
        0, description="Change in interactive element count"
    )
    
    @property
    def has_significant_changes(self) -> bool:
        """Check if significant UI changes occurred."""
        return (
            self.url_changed or
            self.modal_opened or
            self.modal_closed or
            bool(self.new_regions) or
            bool(self.removed_regions) or
            bool(self.alerts_added)
        )


class StateTransition(BaseModel):
    """
    Records the state transition caused by a user interaction.
    
    Links a step to its before/after states and observed changes.
    """
    transition_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique transition identifier"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Transition timestamp"
    )
    
    trigger_step_id: str = Field(..., description="Step that triggered transition")
    before_state_id: str = Field(..., description="State snapshot before interaction")
    after_state_id: str = Field(..., description="State snapshot after interaction")
    
    observed_changes: ObservedChanges = Field(
        default_factory=ObservedChanges,
        description="Detailed change breakdown"
    )
    
    dom_diff_id: Optional[str] = Field(
        None, description="Associated DOM diff ID"
    )
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)


class SemanticPageLabels(BaseModel):
    """
    Rule-based semantic classification of the current page.
    
    Labels are determined by structural analysis, not AI inference.
    """
    labels: list[str] = Field(
        default_factory=list,
        description="Semantic page labels"
    )
    confidence_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Rule match scores per label"
    )
    applied_rules: list[str] = Field(
        default_factory=list,
        description="Rules that matched"
    )
    
    def has_label(self, label: str) -> bool:
        """Check if page has a specific label."""
        return label in self.labels
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)
