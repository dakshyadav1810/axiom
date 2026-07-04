"""
DOM Snapshot Models for Axiome Recording Engine.

Pydantic models for capturing full DOM tree snapshots and
computing structural differences between snapshots.
"""

from datetime import datetime, timezone
from typing import Literal, Optional
import uuid

from pydantic import BaseModel, Field


class DOMNode(BaseModel):
    """
    Represents a single DOM element in the snapshot.
    
    Contains structural and semantic information for comparison.
    """
    node_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique node identifier"
    )
    xpath: str = Field(..., description="Stable XPath to element")
    tag: str = Field(..., description="HTML tag name")
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Element attributes"
    )
    text: Optional[str] = Field(None, description="Direct text content")
    role: Optional[str] = Field(None, description="ARIA role")
    visible: bool = Field(True, description="Element visibility")
    children_ids: list[str] = Field(
        default_factory=list,
        description="Child node IDs"
    )
    parent_id: Optional[str] = Field(None, description="Parent node ID")
    depth: int = Field(0, description="Depth in DOM tree")


class DOMSnapshot(BaseModel):
    """
    Complete DOM tree snapshot at a point in time.
    
    Provides a serializable representation of the page structure
    for diff computation and analysis.
    """
    snapshot_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique snapshot identifier"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Capture timestamp"
    )
    url: str = Field(..., description="Page URL at capture time")
    
    nodes: list[DOMNode] = Field(
        default_factory=list,
        description="All DOM nodes"
    )
    root_id: Optional[str] = Field(None, description="Root node ID")
    node_count: int = Field(0, description="Total node count")
    max_depth: int = Field(0, description="Maximum tree depth")
    
    def get_node_by_xpath(self, xpath: str) -> Optional[DOMNode]:
        """Find a node by its XPath."""
        for node in self.nodes:
            if node.xpath == xpath:
                return node
        return None
    
    def get_nodes_by_tag(self, tag: str) -> list[DOMNode]:
        """Get all nodes with a specific tag."""
        return [n for n in self.nodes if n.tag.lower() == tag.lower()]
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)


class DOMNodeChange(BaseModel):
    """
    Represents a single node change in a DOM diff.
    """
    xpath: str = Field(..., description="XPath to affected node")
    tag: str = Field(..., description="Element tag name")
    change_type: Literal["added", "removed", "modified"] = Field(
        ..., description="Type of change"
    )
    details: Optional[str] = Field(None, description="Change details")


class TextChange(BaseModel):
    """
    Represents a text content change.
    """
    xpath: str = Field(..., description="XPath to element")
    before: Optional[str] = Field(None, description="Text before change")
    after: Optional[str] = Field(None, description="Text after change")


class AttributeChange(BaseModel):
    """
    Represents an attribute value change.
    """
    xpath: str = Field(..., description="XPath to element")
    attribute: str = Field(..., description="Attribute name")
    before: Optional[str] = Field(None, description="Value before change")
    after: Optional[str] = Field(None, description="Value after change")


class DOMDiff(BaseModel):
    """
    Difference between two DOM snapshots.
    
    Provides a structured view of all changes for analysis
    and state transition tracking.
    """
    diff_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique diff identifier"
    )
    before_snapshot_id: str = Field(..., description="Before snapshot ID")
    after_snapshot_id: str = Field(..., description="After snapshot ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Diff computation timestamp"
    )
    
    added_nodes: list[DOMNodeChange] = Field(
        default_factory=list,
        description="Nodes added to DOM"
    )
    removed_nodes: list[DOMNodeChange] = Field(
        default_factory=list,
        description="Nodes removed from DOM"
    )
    modified_nodes: list[DOMNodeChange] = Field(
        default_factory=list,
        description="Nodes with structural changes"
    )
    text_changes: list[TextChange] = Field(
        default_factory=list,
        description="Text content changes"
    )
    attribute_changes: list[AttributeChange] = Field(
        default_factory=list,
        description="Attribute value changes"
    )
    
    @property
    def has_changes(self) -> bool:
        """Check if any changes occurred."""
        return bool(
            self.added_nodes or
            self.removed_nodes or
            self.modified_nodes or
            self.text_changes or
            self.attribute_changes
        )
    
    @property
    def change_count(self) -> int:
        """Total number of changes."""
        return (
            len(self.added_nodes) +
            len(self.removed_nodes) +
            len(self.modified_nodes) +
            len(self.text_changes) +
            len(self.attribute_changes)
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)
