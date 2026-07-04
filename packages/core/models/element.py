"""
Element-related Pydantic models for Axiome Recording Engine.

Contains models for capturing comprehensive element snapshots
including semantic signals, structural attributes, and layout metadata.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """
    Element bounding box coordinates and dimensions.
    
    Represents the visual rectangle occupied by an element
    relative to the viewport.
    
    Attributes:
        x: Left edge X coordinate in pixels
        y: Top edge Y coordinate in pixels
        width: Element width in pixels
        height: Element height in pixels
    """
    x: float = Field(..., description="Left edge X coordinate")
    y: float = Field(..., description="Top edge Y coordinate")
    width: float = Field(..., ge=0, description="Element width")
    height: float = Field(..., ge=0, description="Element height")


class ElementSnapshot(BaseModel):
    """
    Comprehensive snapshot of a DOM element at interaction time.
    
    Captures semantic signals, accessibility metadata, structural
    attributes, and layout information needed for deterministic
    element resolution during test replay.
    
    Attributes:
        tag: HTML tag name (e.g., 'button', 'input', 'a')
        text: Visible text content of the element
        normalized_text: Lowercase, whitespace-normalized text
        role: ARIA role or implicit semantic role
        aria_label: Explicit ARIA label if present
        attributes: Key-value map of HTML attributes
        bounding_box: Visual position and dimensions
        is_visible: Whether element is visually visible
        is_enabled: Whether element is enabled/interactive
    """
    tag: str = Field(..., description="HTML tag name")
    text: Optional[str] = Field(None, description="Visible text content")
    normalized_text: Optional[str] = Field(
        None, 
        description="Lowercase, whitespace-normalized text"
    )
    role: Optional[str] = Field(None, description="ARIA or semantic role")
    aria_label: Optional[str] = Field(None, description="ARIA label attribute")
    attributes: dict[str, Any] = Field(
        default_factory=dict, 
        description="HTML attributes"
    )
    bounding_box: Optional[BoundingBox] = Field(
        None, 
        description="Element position and size"
    )
    is_visible: bool = Field(True, description="Element visibility state")
    is_enabled: bool = Field(True, description="Element enabled state")
    nearby_text: Optional[str] = Field(
        None,
        description="Text from nearest row/card/list-item container for disambiguation"
    )
    
    # Semantic field name derived from input[type] — maps raw HTML type values to
    # human-readable field labels used as a friendly-name fallback.
    _INPUT_TYPE_LABELS: dict[str, str] = {
        "email": "Email",
        "password": "Password",
        "search": "Search",
        "tel": "Phone",
        "url": "URL",
        "number": "Number",
        "date": "Date",
        "time": "Time",
        "file": "File",
        "checkbox": "Checkbox",
        "radio": "Radio",
        "range": "Slider",
        "color": "Color picker",
        "text": "Text field",
        "submit": None,   # handled via value/text
        "button": None,   # handled via value/text
        "reset": "Reset",
    }

    @staticmethod
    def _humanize_token(raw: str) -> str:
        """Convert a data-testid / class / id token to Title Case human text.

        E.g. 'login-submit-btn' → 'Login Submit', 'searchBar' → 'Search Bar'.
        """
        import re
        # Split on hyphens, underscores, and camelCase boundaries
        parts = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw)
        parts = re.split(r'[-_\s]+', parts)
        # Drop pure noise suffixes
        noise = {"btn", "button", "input", "field", "wrap", "wrapper", "container",
                 "el", "elem", "comp", "component", "id", "ref"}
        meaningful = [p for p in parts if p.lower() not in noise and len(p) > 1]
        return " ".join(p.capitalize() for p in meaningful) if meaningful else ""

    def get_friendly_name(self) -> str:
        """
        Generate a human-readable name for this element.

        Priority order:
        1. aria_label
        2. visible text content (truncated)
        3. placeholder attribute  (inputs/textareas)
        4. Input type-derived label  (e.g. "Email", "Password")
        5. submit/button value attribute
        6. alt attribute  (image buttons)
        7. title attribute
        8. Humanised data-testid / data-cy / data-qa
        9. id attribute (humanised)
        10. name attribute (humanised)
        11. Tag-based generic label (never raw tag)
        """
        if self.aria_label:
            return self.aria_label[:50]

        if self.text:
            clean_text = self.text.strip()[:50]
            if clean_text:
                return clean_text

        attrs = self.attributes
        tag = self.tag.lower()

        # Placeholder is highly descriptive for input/textarea
        placeholder = attrs.get("placeholder", "")
        if placeholder:
            return placeholder[:50]

        # Input type → semantic label
        input_type = attrs.get("type", "").lower()
        if tag == "input" and input_type:
            if input_type in ("submit", "button", "reset"):
                # use value attribute text e.g. <input type="submit" value="Log in">
                val = attrs.get("value", "").strip()
                if val:
                    return val[:50]
            type_label = self._INPUT_TYPE_LABELS.get(input_type)
            if type_label:
                return type_label

        # alt on images (icon buttons)
        alt = attrs.get("alt", "").strip()
        if alt and alt.lower() not in ("", "image", "icon"):
            return alt[:50]

        # title attribute
        title = attrs.get("title", "").strip()
        if title:
            return title[:50]

        # data-testid / data-cy / data-qa
        for key in ("data-testid", "data-cy", "data-qa", "data-test"):
            val = attrs.get(key, "").strip()
            if val:
                humanised = self._humanize_token(val)
                if humanised:
                    return humanised[:50]

        # id (humanised)
        if "id" in attrs:
            humanised = self._humanize_token(attrs["id"])
            if humanised:
                return humanised[:50]

        # name (humanised)
        if "name" in attrs:
            humanised = self._humanize_token(attrs["name"])
            if humanised:
                return humanised[:50]

        # Tag-based generic — never return the raw tag string
        _TAG_GENERICS: dict[str, str] = {
            "button": "Button",
            "a": "Link",
            "input": "Text field",
            "textarea": "Text area",
            "select": "Dropdown",
            "img": "Image",
            "svg": "Icon",
            "form": "Form",
        }
        return _TAG_GENERICS.get(tag, "Element")


class ContextNode(BaseModel):
    """
    Structured ancestor node for semantic context path.
    
    Represents a single container in the element's ancestry,
    capturing its semantic identity and attributes.
    
    Attributes:
        tag: HTML tag name
        role: ARIA role (if significant)
        class_name: CSS classes (if significant)
        attributes: Other identifying attributes (id, test-id)
    """
    tag: str = Field(..., description="HTML tag name")
    role: Optional[str] = Field(None, description="ARIA role")
    class_name: Optional[str] = Field(None, description="CSS classes")
    attributes: dict[str, Any] = Field(
        default_factory=dict, 
        description="Identifying attributes"
    )
