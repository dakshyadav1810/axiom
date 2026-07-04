from __future__ import annotations

"""
Affordance Resolver - Validates that elements can perform actions.

This resolver answers: "Can this element actually perform this action?"

This is a VALIDATION-ONLY resolver. It never selects, only filters.

Checks:
- Is visible
- Is enabled
- Is clickable/focusable
- Pointer events enabled
- Correct input type for typing
"""
from typing import List, Union, Tuple

from .base import BaseResolver
from ..models.resolver_models import DOMElement, ResolverCandidate, ActionNode, ActionType


# Tags that are inherently clickable
CLICKABLE_TAGS = {"button", "a", "input", "select", "textarea", "label", "summary"}

# Tags that accept text input
TYPEABLE_TAGS = {"input", "textarea"}

# Input types that accept text
TYPEABLE_INPUT_TYPES = {
    "text", "password", "email", "search", "tel", "url", "number", "date",
    "datetime-local", "month", "week", "time"
}

# Roles that are typically clickable
CLICKABLE_ROLES = {"button", "link", "menuitem", "tab", "checkbox", "radio", "option", "switch"}


class AffordanceResolver(BaseResolver):
    """
    Affordance resolver validates that elements can be interacted with.
    
    This resolver ONLY FILTERS candidates. It does not select or rank.
    Elements that fail affordance checks are removed from consideration.
    """
    
    name = "affordance"
    
    def resolve(
        self,
        candidates: Union[List[DOMElement], List[ResolverCandidate]],
        action: ActionNode,
        context: dict,
    ) -> List[ResolverCandidate]:
        """
        Filter candidates based on affordance validation.
        
        Only candidates that can perform the action pass through.
        """
        results = []
        
        for candidate in candidates:
            # Handle both DOMElement and ResolverCandidate inputs
            if isinstance(candidate, ResolverCandidate):
                resolver_candidate = candidate
                element = candidate.element
            else:
                resolver_candidate = ResolverCandidate(
                    element=candidate,
                    score=0.0,
                    reasons=[],
                )
                element = candidate
            
            # Check affordance
            is_valid, reason = self._validate_affordance(element, action.type)
            
            if is_valid:
                resolver_candidate.affordance_passed = True
                resolver_candidate.reasons.append("affordance_passed")
                results.append(resolver_candidate)
            else:
                # Log why it was filtered (for debugging)
                resolver_candidate.affordance_passed = False
                resolver_candidate.reasons.append(f"affordance_failed:{reason}")
                # Don't add to results - this element is filtered out
        
        return results
    
    def _validate_affordance(
        self,
        element: DOMElement,
        action_type: ActionType,
    ) -> Tuple[bool, str]:
        """
        Validate that element can perform the action.
        
        Returns (is_valid, failure_reason).
        """
        # Basic visibility check
        if not element.is_visible:
            return False, "not_visible"
        
        # Basic enabled check
        if not element.is_enabled:
            return False, "disabled"
        
        # Action-specific checks
        if action_type == ActionType.CLICK:
            return self._can_click(element)
        elif action_type == ActionType.HOVER:
            return self._can_hover(element)
        elif action_type == ActionType.TYPE:
            return self._can_type(element)
        elif action_type == ActionType.SELECT:
            return self._can_select(element)
        elif action_type == ActionType.KEYPRESS:
            return self._can_keypress(element)
        elif action_type == ActionType.NAVIGATE:
            # Navigation doesn't need element affordance
            return True, ""
        elif action_type == ActionType.WAIT:
            # Wait doesn't need element affordance
            return True, ""
        elif action_type == ActionType.GO_BACK:
            return True, ""
        elif action_type == ActionType.REFRESH:
            return True, ""
        elif action_type == ActionType.WAIT_FOR_STABLE:
            return True, ""
        elif action_type == ActionType.SWITCH_CONTEXT:
            return True, ""
        elif action_type == ActionType.SUBMIT:
            return self._can_submit(element)
        
        return True, ""

    def _can_hover(self, element: DOMElement) -> Tuple[bool, str]:
        """Hover follows click-like affordance requirements."""
        return self._can_click(element)

    def _can_submit(self, element: DOMElement) -> Tuple[bool, str]:
        """Check if element is submittable."""
        tag = element.tag.lower()
        
        # Forms are submittable
        if tag == "form":
            return True, ""
            
        # Inputs/Buttons are submittable (via click or enter)
        if tag in CLICKABLE_TAGS:
            return True, ""
            
        # Check standard interactive roles
        if element.role and element.role.lower() in CLICKABLE_ROLES:
            return True, ""
            
        return False, f"not_submittable:{tag}"
    
    def _can_click(self, element: DOMElement) -> Tuple[bool, str]:
        """Check if element is clickable."""
        tag = element.tag.lower()
        
        # Check inherently clickable tags
        if tag in CLICKABLE_TAGS:
            return True, ""
        
        # Check clickable roles
        if element.role and element.role.lower() in CLICKABLE_ROLES:
            return True, ""
        
        # Check for click handler (including cursor: pointer from extraction)
        if element.has_click_handler:
            return True, ""
        
        # Check for focusable (can receive clicks)
        if element.is_focusable:
            return True, ""
        
        # Check for tabindex (makes element interactive)
        if element.attributes.get("tabindex") is not None:
            return True, ""
        
        # Check for contenteditable
        if element.attributes.get("contenteditable") == "true":
            return True, ""
        
        # Check for common interactive data attributes
        if any(element.attributes.get(attr) for attr in ("data-action", "data-toggle", "data-dismiss")):
            return True, ""
        
        # Element is not inherently interactive — filter it out
        return False, f"not_clickable:{tag}"
    
    def _can_type(self, element: DOMElement) -> Tuple[bool, str]:
        """Check if element accepts text input."""
        tag = element.tag.lower()
        
        # Check for contenteditable (e.g. rich text editors)
        if element.attributes.get("contenteditable") == "true":
            return True, ""
        
        # Must be a typeable tag
        if tag not in TYPEABLE_TAGS:
            return False, f"not_typeable:{tag}"
        
        # Must be focusable
        if not element.is_focusable and element.attributes.get("tabindex") is None:
            return False, "not_focusable"
        
        # For input elements, check type
        if tag == "input":
            input_type = element.attributes.get("type", "text").lower()
            if input_type not in TYPEABLE_INPUT_TYPES:
                return False, f"non_text_input:{input_type}"
        
        # Check for readonly
        if element.attributes.get("readonly") is not None:
            return False, "readonly"
        
        return True, ""

    def _can_select(self, element: DOMElement) -> Tuple[bool, str]:
        """Check if element supports option selection."""
        tag = element.tag.lower()
        if tag == "select":
            return True, ""
        if element.role and element.role.lower() in {"combobox", "listbox", "option"}:
            return True, ""
        if element.attributes.get("aria-haspopup") in {"listbox", "menu", "true"}:
            return True, ""
        return False, f"not_selectable:{tag}"

    def _can_keypress(self, element: DOMElement) -> Tuple[bool, str]:
        """Check if element can receive key events."""
        tag = element.tag.lower()
        if element.attributes.get("contenteditable") == "true":
            return True, ""
        if tag in {"input", "textarea", "select", "button", "a", "form"}:
            return True, ""
        if element.role and element.role.lower() in (CLICKABLE_ROLES | {"textbox", "combobox", "searchbox"}):
            return True, ""
        if element.is_focusable or element.attributes.get("tabindex") is not None:
            return True, ""
        return False, f"not_keypressable:{tag}"
