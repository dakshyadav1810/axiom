"""
JSON Serializer for Axiome Recording Engine.

Handles serialization of Flow objects to deterministic JSON output.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from ..models import Flow


class JsonSerializer:
    """
    Serializes Flow objects to JSON format.
    
    Produces deterministic, well-formatted JSON output suitable
    for storage and later replay.
    
    Features:
    - Consistent key ordering
    - Proper datetime formatting (ISO 8601)
    - Configurable indentation
    - File saving with atomic writes
    
    Example:
        serializer = JsonSerializer()
        json_str = serializer.serialize(flow)
        serializer.save_to_file(flow, "output.json")
    """
    
    def __init__(self, indent: int = 2, sort_keys: bool = False):
        """
        Initialize the serializer.
        
        Args:
            indent: JSON indentation level (default 2)
            sort_keys: Whether to sort object keys
        """
        self._indent = indent
        self._sort_keys = sort_keys
    
    def serialize(self, flow: Flow) -> str:
        """
        Serialize a Flow to JSON string.
        
        Args:
            flow: Flow object to serialize
            
        Returns:
            JSON string representation
        """
        # Use Pydantic's model_dump with custom serialization
        data = flow.model_dump(mode="json")
        
        return json.dumps(
            data,
            indent=self._indent,
            sort_keys=self._sort_keys,
            ensure_ascii=False,
            default=self._json_default
        )
    
    def serialize_to_dict(self, flow: Flow) -> dict[str, Any]:
        """
        Serialize a Flow to a dictionary.
        
        Args:
            flow: Flow object to serialize
            
        Returns:
            Dictionary representation
        """
        return flow.model_dump(mode="json")
    
    def save_to_file(
        self,
        flow: Flow,
        path: Union[str, Path],
        atomic: bool = True
    ) -> None:
        """
        Save a Flow to a JSON file.
        
        Args:
            flow: Flow object to save
            path: Output file path
            atomic: Use atomic write (write to temp, then rename)
        """
        path = Path(path)
        json_content = self.serialize(flow)
        
        if atomic:
            # Write to temp file first
            temp_path = path.with_suffix(".tmp")
            try:
                temp_path.write_text(json_content, encoding="utf-8")
                temp_path.rename(path)
            except Exception:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise
        else:
            path.write_text(json_content, encoding="utf-8")
    
    def load_from_file(self, path: Union[str, Path]) -> Flow:
        """
        Load a Flow from a JSON file.
        
        Args:
            path: Input file path
            
        Returns:
            Flow object
        """
        path = Path(path)
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        return Flow.model_validate(data)
    
    def _json_default(self, obj: Any) -> Any:
        """Default JSON serializer for unsupported types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
