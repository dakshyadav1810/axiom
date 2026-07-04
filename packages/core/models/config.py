"""
Configuration Models for Axiome Recording Engine.

Pydantic models for recorder configuration options.
"""

from pydantic import BaseModel, Field


class RecorderConfig(BaseModel):
    """
    Configuration options for the state-aware recorder.
    
    Controls which features are enabled and performance tuning.
    """
    # Feature toggles
    enable_state_tracking: bool = Field(
        True, description="Enable page state snapshot capture"
    )
    enable_dom_snapshots: bool = Field(
        True, description="Enable full DOM snapshot capture"
    )
    enable_interaction_graph: bool = Field(
        True, description="Enable interaction graph building"
    )
    enable_semantic_labels: bool = Field(
        True, description="Enable semantic page classification"
    )
    
    # Performance tuning
    dom_max_depth: int = Field(
        50, description="Maximum DOM tree traversal depth"
    )
    dom_max_nodes: int = Field(
        5000, description="Maximum nodes to capture in DOM snapshot"
    )
    stability_wait_ms: int = Field(
        500, description="Milliseconds to wait for page stability after interaction"
    )
    
    # Filtering
    exclude_hidden_elements: bool = Field(
        True, description="Exclude hidden elements from snapshots"
    )
    exclude_script_style: bool = Field(
        True, description="Exclude script and style elements"
    )
    
    # Output options
    include_dom_in_step: bool = Field(
        False, description="Include full DOM snapshots in step output (large)"
    )
    include_graph_in_step: bool = Field(
        True, description="Include interaction graph in step output"
    )
    
    # Use ConfigDict for Pydantic V2
    model_config = {"frozen": False}


# Default configuration instance
DEFAULT_CONFIG = RecorderConfig()
