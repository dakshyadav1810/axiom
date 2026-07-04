"""
State Snapshot Models for Axiome Recording Engine.

Pydantic models for capturing deterministic page state information
including UI regions, forms, modals, alerts, and navigation structure.
"""

from datetime import datetime, timezone
from typing import Literal, Optional
import uuid

from pydantic import BaseModel, Field


class PageIdentity(BaseModel):
    """
    Identifies the current page location and title.
    
    Provides normalized URL components for matching.
    """
    url: str = Field(..., description="Full page URL")
    url_path: str = Field(..., description="URL path component")
    domain: str = Field(..., description="Domain/hostname")
    title: str = Field(..., description="Document title")


class UIRegion(BaseModel):
    """
    Represents a semantic UI region on the page.
    
    Regions are detected via tag names and ARIA roles.
    """
    region_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique region identifier"
    )
    region_type: Literal["form", "dialog", "navigation", "content", "alert", "modal", "listing"] = Field(
        ..., description="Semantic region type"
    )
    role: Optional[str] = Field(None, description="ARIA role if present")
    label: Optional[str] = Field(None, description="Accessible label")
    visible: bool = Field(True, description="Visibility state")
    xpath: Optional[str] = Field(None, description="XPath for region element")


class FormState(BaseModel):
    """
    Captures form element state including fields and validity.
    """
    form_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique form identifier"
    )
    xpath: Optional[str] = Field(None, description="XPath to form element")
    field_count: int = Field(0, description="Number of input fields")
    required_fields: list[str] = Field(
        default_factory=list,
        description="Names of required fields"
    )
    submit_present: bool = Field(False, description="Has submit button")
    validity_state: Literal["valid", "invalid", "unknown"] = Field(
        "unknown", description="Form validation state"
    )


class ModalState(BaseModel):
    """
    Tracks modal/dialog presence on the page.
    """
    has_modal: bool = Field(False, description="Modal is currently open")
    modal_roles: list[str] = Field(
        default_factory=list,
        description="Roles of open modals (dialog, alertdialog, etc.)"
    )


class AlertInfo(BaseModel):
    """
    Represents a detected alert or notification.
    """
    type: Literal["error", "success", "info", "warning"] = Field(
        ..., description="Alert severity type"
    )
    text: str = Field(..., description="Alert text content")
    xpath: Optional[str] = Field(None, description="XPath to alert element")


class InteractionSummary(BaseModel):
    """
    Summary counts of interactive elements on the page.
    """
    clickable_count: int = Field(0, description="Number of clickable elements")
    input_count: int = Field(0, description="Number of input fields")
    select_count: int = Field(0, description="Number of select dropdowns")
    checkbox_count: int = Field(0, description="Number of checkboxes")
    radio_count: int = Field(0, description="Number of radio buttons")
    link_count: int = Field(0, description="Number of links")


class NavigationStructure(BaseModel):
    """
    Describes the navigation layout of the page.
    """
    sidebar_present: bool = Field(False, description="Sidebar navigation exists")
    top_nav_present: bool = Field(False, description="Top navigation bar exists")
    breadcrumbs_present: bool = Field(False, description="Breadcrumb navigation exists")
    footer_nav_present: bool = Field(False, description="Footer navigation exists")


class StateSnapshot(BaseModel):
    """
    Complete page state snapshot at a point in time.
    
    Captures all deterministic UI state information for
    comparison and analysis.
    """
    state_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique snapshot identifier"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Capture timestamp"
    )
    
    page_identity: PageIdentity = Field(..., description="Page location info")
    ui_regions: list[UIRegion] = Field(
        default_factory=list,
        description="Detected UI regions"
    )
    forms: list[FormState] = Field(
        default_factory=list,
        description="Form states"
    )
    modal_state: ModalState = Field(
        default_factory=ModalState,
        description="Modal/dialog state"
    )
    alerts: list[AlertInfo] = Field(
        default_factory=list,
        description="Active alerts/notifications"
    )
    interaction_summary: InteractionSummary = Field(
        default_factory=InteractionSummary,
        description="Interactive element counts"
    )
    navigation_structure: NavigationStructure = Field(
        default_factory=NavigationStructure,
        description="Navigation layout"
    )
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)
