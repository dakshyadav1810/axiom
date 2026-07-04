"""
Interaction Graph Models for Axiome Recording Engine.

Pydantic models for representing interactive elements and their
relationships within the page structure.
"""

from datetime import datetime, timezone
from typing import Literal, Optional
import uuid

from pydantic import BaseModel, Field


class InteractionNode(BaseModel):
    """
    Represents a single interactive element in the graph.
    
    Nodes are elements that can receive user input or trigger actions.
    """
    node_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique node identifier"
    )
    node_type: Literal["button", "link", "input", "select", "checkbox", "radio", "textarea"] = Field(
        ..., description="Element interaction type"
    )
    text: Optional[str] = Field(None, description="Visible text content")
    role: Optional[str] = Field(None, description="ARIA role")
    aria_label: Optional[str] = Field(None, description="Accessible label")
    visible: bool = Field(True, description="Element is visible")
    enabled: bool = Field(True, description="Element is enabled/not disabled")
    container_region_id: Optional[str] = Field(
        None, description="Parent UI region ID"
    )
    xpath: Optional[str] = Field(None, description="XPath to element")
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Key element attributes"
    )


class GraphEdge(BaseModel):
    """
    Represents a containment relationship between region and node.
    """
    parent_region_id: str = Field(..., description="Container region ID")
    child_node_id: str = Field(..., description="Contained node ID")
    relation: Literal["contains"] = Field(
        "contains", description="Relationship type"
    )


class InteractionGraph(BaseModel):
    """
    Complete graph of interactive elements on a page.
    
    Provides a structured view of all possible user interactions
    and their container relationships.
    """
    graph_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique graph identifier"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Capture timestamp"
    )
    state_id: Optional[str] = Field(
        None, description="Associated state snapshot ID"
    )
    
    nodes: list[InteractionNode] = Field(
        default_factory=list,
        description="Interactive element nodes"
    )
    edges: list[GraphEdge] = Field(
        default_factory=list,
        description="Containment relationships"
    )
    
    @property
    def node_count(self) -> int:
        """Total number of interactive nodes."""
        return len(self.nodes)
    
    def get_nodes_by_type(self, node_type: str) -> list[InteractionNode]:
        """Get all nodes of a specific type."""
        return [n for n in self.nodes if n.node_type == node_type]
    
    def get_nodes_in_region(self, region_id: str) -> list[InteractionNode]:
        """Get all nodes contained in a specific region."""
        node_ids = {e.child_node_id for e in self.edges if e.parent_region_id == region_id}
        return [n for n in self.nodes if n.node_id in node_ids]
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)
