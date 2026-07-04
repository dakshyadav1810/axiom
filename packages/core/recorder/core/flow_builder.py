"""
Flow Builder for Axiome Recording Engine.

Manages Flow state during recording, including step accumulation
and flow metadata.
"""

from datetime import datetime
from typing import Optional
import uuid

from ..models import Flow, Step, GeneralSettings, GeneralizationLevel


class FlowBuilder:
    """
    Builds and manages Flow state during recording.
    
    Provides methods to create flows, add steps, and retrieve
    the complete flow structure.
    
    Example:
        builder = FlowBuilder()
        flow = builder.create_flow("Login Flow", "project-1", "https://example.com")
        builder.add_step(step1)
        builder.add_step(step2)
        complete_flow = builder.get_flow()
    """
    
    def __init__(self):
        """Initialize the flow builder."""
        self._flow: Optional[Flow] = None
        self._step_count = 0
    
    @property
    def has_flow(self) -> bool:
        """Check if a flow has been created."""
        return self._flow is not None
    
    @property
    def step_count(self) -> int:
        """Get the number of steps in the current flow."""
        return self._step_count
    
    def create_flow(
        self,
        flow_name: str,
        project_id: str,
        base_url: str,
        environment: Optional[str] = None,
        default_generalization: GeneralizationLevel = GeneralizationLevel.MODERATE
    ) -> Flow:
        """
        Create a new flow.
        
        Args:
            flow_name: Human-readable name for the flow
            project_id: Parent project identifier
            base_url: Starting URL for the flow
            environment: Optional environment name
            default_generalization: Default matching strictness
            
        Returns:
            The newly created Flow instance
        """
        self._flow = Flow(
            flow_id=str(uuid.uuid4()),
            project_id=project_id,
            flow_name=flow_name,
            created_at=datetime.utcnow(),
            base_url=base_url,
            general_settings=GeneralSettings(
                default_generalization_level=default_generalization,
                environment=environment
            ),
            steps=[]
        )
        self._step_count = 0
        
        return self._flow
    
    def add_step(self, step: Step) -> None:
        """
        Add a step to the current flow.
        
        Automatically updates the step order.
        
        Args:
            step: Step to add
            
        Raises:
            RuntimeError: If no flow has been created
        """
        if not self._flow:
            raise RuntimeError("No flow created. Call create_flow() first.")
        
        self._step_count += 1
        step.order = self._step_count
        self._flow.steps.append(step)
    
    def get_flow(self) -> Optional[Flow]:
        """
        Get the current flow.
        
        Returns:
            The Flow instance or None if not created
        """
        return self._flow
    
    def reset(self) -> None:
        """Reset the builder, clearing any existing flow."""
        self._flow = None
        self._step_count = 0
    
    def get_last_step(self) -> Optional[Step]:
        """
        Get the most recently added step.
        
        Returns:
            The last Step or None if no steps
        """
        if self._flow and self._flow.steps:
            return self._flow.steps[-1]
        return None
    
    def remove_last_step(self) -> Optional[Step]:
        """
        Remove and return the last step.
        
        Useful for undoing the last recorded interaction.
        
        Returns:
            The removed Step or None if no steps
        """
        if self._flow and self._flow.steps:
            self._step_count -= 1
            return self._flow.steps.pop()
        return None
    
    def update_flow_metadata(
        self,
        flow_name: Optional[str] = None,
        environment: Optional[str] = None
    ) -> None:
        """
        Update flow metadata.
        
        Args:
            flow_name: New flow name (optional)
            environment: New environment name (optional)
        """
        if not self._flow:
            return
        
        if flow_name:
            self._flow.flow_name = flow_name
        
        if environment:
            self._flow.general_settings.environment = environment
