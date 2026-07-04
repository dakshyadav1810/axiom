"""
Context Path Builder for Axiome Recording Engine.

Derives semantic ancestor chains from DOM elements to provide
contextual information for element resolution.
"""

from typing import Any, Optional

from playwright.async_api import Page, ElementHandle
from ..models import ContextNode, ElementSnapshot, BoundingBox, Selectors


class ContextPathBuilder:
    """
    Builds semantic context paths from DOM element ancestry.
    
    Context paths represent the meaningful container hierarchy
    of an element, enabling semantic matching even when DOM
    structure changes.
    
    Rules:
    - Maximum depth of 5 ancestors
    - Prioritizes semantic containers (form, dialog, section, etc.)
    - Deterministic ordering (child to ancestor)
    - Uses id, aria-label, role, and tag name for identification
    
    Example:
        builder = ContextPathBuilder()
        path = await builder.build_from_data(element_data)
        # Returns: [ContextNode(tag="form", attributes={"id": "login-form"}), ...]
    """
    
    # Semantic container tags to prioritize
    SEMANTIC_TAGS = frozenset({
        "form", "dialog", "section", "article", "aside", "nav",
        "main", "header", "footer", "figure", "fieldset",
        "details", "menu", "search"
    })
    
    # Semantic roles to prioritize
    SEMANTIC_ROLES = frozenset({
        "dialog", "form", "navigation", "main", "region", 
        "complementary", "banner", "contentinfo", "search",
        "application", "document", "feed", "grid", "list", 
        "menu", "menubar", "tablist", "toolbar", "tree", "treegrid"
    })
    
    # Maximum ancestor depth
    MAX_DEPTH = 5
    
    def build_from_data(self, element_data: dict[str, Any]) -> list[ContextNode]:
        """
        Build context path from element data containing ancestry.
        
        The element_data should include an 'ancestors' field with
        parent element information.
        
        Args:
            element_data: Raw element data from JavaScript
            
        Returns:
            List of ContextNodes (child to root)
        """
        ancestors = element_data.get("ancestors", [])
        context_path: list[ContextNode] = []
        
        for ancestor in ancestors[:self.MAX_DEPTH]:
            node = self._create_context_node(ancestor)
            if node:
                context_path.append(node)
        
        return context_path
    
    def _create_context_node(self, ancestor: dict[str, Any]) -> Optional[ContextNode]:
        """
        Create a ContextNode if the ancestor is a meaningful container.
        
        Criteria:
        1. Has ID
        2. Has aria-label
        3. Has data-testid
        4. Is a semantic tag
        5. Has a semantic role
        6. Has data-* attributes with identifying info
        
        Args:
            ancestor: Ancestor element data
            
        Returns:
            ContextNode or None if not significant
        """
        tag = ancestor.get("tag", "").lower()
        attrs = ancestor.get("attributes", {})
        role = ancestor.get("role") or attrs.get("role")
        class_name = attrs.get("class")
        
        # Check significance
        has_id = bool(attrs.get("id"))
        has_aria_label = bool(attrs.get("aria-label"))
        has_test_id = any(k in attrs for k in ["data-testid", "data-test-id", "data-cy"])
        has_data_attrs = any(k.startswith("data-") for k in attrs if k not in ("data-testid", "data-test-id", "data-cy"))
        is_semantic_tag = tag in self.SEMANTIC_TAGS
        is_semantic_role = role in self.SEMANTIC_ROLES
        
        if not (has_id or has_aria_label or has_test_id or is_semantic_tag or is_semantic_role or has_data_attrs):
            return None
            
        # Filter attributes to likely stable identifiers
        filtered_attrs = {}
        if elem_id := attrs.get("id"):
            filtered_attrs["id"] = elem_id
        
        if aria_label := attrs.get("aria-label"):
            filtered_attrs["aria-label"] = aria_label
            
        for key in ["data-testid", "data-test-id", "data-cy", "name", "title"]:
            if val := attrs.get(key):
                filtered_attrs[key] = val
        
        # Include data-* attributes for richer context
        for key, val in attrs.items():
            if key.startswith("data-") and key not in filtered_attrs:
                filtered_attrs[key] = val
        
        # Include aria-* attributes beyond aria-label
        for key, val in attrs.items():
            if key.startswith("aria-") and key not in filtered_attrs:
                filtered_attrs[key] = val
                
        return ContextNode(
            tag=tag,
            role=role,
            class_name=class_name,
            attributes=filtered_attrs
        )
    
    async def build_from_handle(
        self, 
        page: Page, 
        element_handle: ElementHandle
    ) -> list[ContextNode]:
        """
        Build context path from a Playwright ElementHandle.
        
        Evaluates JavaScript to traverse DOM ancestry and extract
        semantic container information.
        
        Args:
            page: Playwright Page instance
            element_handle: Handle to the target DOM element
            
        Returns:
            List of semantic ContextNodes
        """
        ancestors = await page.evaluate("""
            (element) => {
                const ancestors = [];
                let current = element.parentElement;
                let depth = 0;
                const maxDepth = 5;
                
                const semanticTags = new Set([
                    'form', 'dialog', 'section', 'article', 'aside', 'nav',
                    'main', 'header', 'footer', 'figure', 'fieldset',
                    'details', 'menu', 'search'
                ]);
                
                const semanticRoles = new Set([
                    'dialog', 'form', 'navigation', 'main', 'region', 
                    'complementary', 'banner', 'contentinfo', 'search',
                    'application', 'document', 'feed', 'grid', 'list', 
                    'menu', 'menubar', 'tablist', 'toolbar', 'tree', 'treegrid'
                ]);
                
                while (current && current !== document.body && depth < maxDepth) {
                    const tag = current.tagName.toLowerCase();
                    const attrs = {};
                    
                    for (const attr of current.attributes || []) {
                        attrs[attr.name] = attr.value;
                    }
                    
                    // Only include semantic containers or elements with identifiers
                    const hasId = current.id;
                    const hasAriaLabel = current.getAttribute('aria-label');
                    const hasTestId = current.getAttribute('data-testid') ||
                                      current.getAttribute('data-test-id') ||
                                      current.getAttribute('data-cy');
                    const isSemantic = semanticTags.has(tag);
                    const role = current.getAttribute('role');
                    const hasSemanticRole = role && semanticRoles.has(role);
                    
                    if (hasId || hasAriaLabel || hasTestId || isSemantic || hasSemanticRole) {
                        ancestors.push({
                            tag: tag,
                            role: role,
                            attributes: attrs
                        });
                        depth++;
                    }
                    
                    current = current.parentElement;
                }
                
                return ancestors;
            }
        """, element_handle)
        
        return self.build_from_data({"ancestors": ancestors})
    
    async def build_from_page_position(
        self,
        page: Page,
        x: float,
        y: float
    ) -> list[ContextNode]:
        """
        Build context path from a viewport position.
        
        Uses document.elementFromPoint to find the element at
        the given coordinates and build its context path.
        
        Args:
            page: Playwright Page instance
            x: X coordinate in viewport
            y: Y coordinate in viewport
            
        Returns:
            List of semantic ContextNodes
        """
        ancestors = await page.evaluate("""
            ({x, y}) => {
                const element = document.elementFromPoint(x, y);
                if (!element) return [];
                
                const ancestors = [];
                let current = element.parentElement;
                let depth = 0;
                const maxDepth = 5;
                
                const semanticTags = new Set([
                    'form', 'dialog', 'section', 'article', 'aside', 'nav',
                    'main', 'header', 'footer', 'figure', 'fieldset',
                    'details', 'menu', 'search'
                ]);
                
                const semanticRoles = new Set([
                    'dialog', 'form', 'navigation', 'main', 'region', 
                    'complementary', 'banner', 'contentinfo', 'search',
                    'application', 'document', 'feed', 'grid', 'list', 
                    'menu', 'menubar', 'tablist', 'toolbar', 'tree', 'treegrid'
                ]);
                
                while (current && current !== document.body && depth < maxDepth) {
                    const tag = current.tagName.toLowerCase();
                    const attrs = {};
                    
                    for (const attr of current.attributes || []) {
                        attrs[attr.name] = attr.value;
                    }
                    
                    const hasId = current.id;
                    const hasAriaLabel = current.getAttribute('aria-label');
                    const hasTestId = current.getAttribute('data-testid') ||
                                      current.getAttribute('data-test-id') ||
                                      current.getAttribute('data-cy');
                    const isSemantic = semanticTags.has(tag);
                    const role = current.getAttribute('role');
                    const hasSemanticRole = role && semanticRoles.has(role);
                    
                    if (hasId || hasAriaLabel || hasTestId || isSemantic || hasSemanticRole) {
                        ancestors.push({
                            tag: tag,
                            role: role,
                            attributes: attrs
                        });
                        depth++;
                    }
                    
                    current = current.parentElement;
                }
                
                return ancestors;
            }
        """, {"x": x, "y": y})
        
        return self.build_from_data({"ancestors": ancestors})
