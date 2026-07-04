"""
Element Snapshot Builder for Axiome Recording Engine.

Extracts comprehensive element data from DOM elements via
Playwright's page.evaluate() for rich element snapshots.
"""

from typing import Any, Optional

from playwright.async_api import Page, ElementHandle

from ..models import ElementSnapshot, BoundingBox, Selectors


class ElementSnapshotBuilder:
    """
    Builds comprehensive element snapshots from DOM elements.
    
    Extracts semantic signals, accessibility metadata, structural
    attributes, and layout information for deterministic element
    resolution during test replay.
    
    The builder uses page.evaluate() for extraction, which runs
    JavaScript in the browser context for accurate data capture.
    
    Example:
        builder = ElementSnapshotBuilder()
        snapshot = await builder.build_from_data(element_data)
        selectors = builder.extract_selectors(element_data)
    """
    
    def build_from_data(self, element_data: dict[str, Any]) -> ElementSnapshot:
        """
        Build an ElementSnapshot from raw element data.
        
        The element_data is expected to come from the JavaScript
        capture script in InteractionObserver.
        
        Args:
            element_data: Raw element data from JavaScript
            
        Returns:
            Structured ElementSnapshot instance
        """
        bounding_box = None
        if bb_data := element_data.get("bounding_box"):
            bounding_box = BoundingBox(
                x=bb_data.get("x", 0),
                y=bb_data.get("y", 0),
                width=bb_data.get("width", 0),
                height=bb_data.get("height", 0)
            )
        
        return ElementSnapshot(
            tag=element_data.get("tag", "unknown"),
            text=element_data.get("text"),
            normalized_text=element_data.get("normalized_text"),
            role=element_data.get("role"),
            aria_label=element_data.get("aria_label"),
            attributes=element_data.get("attributes", {}),
            bounding_box=bounding_box,
            is_visible=element_data.get("is_visible", True),
            is_enabled=element_data.get("is_enabled", True),
            nearby_text=element_data.get("nearby_text") or None,
        )
    
    def extract_selectors(self, element_data: dict[str, Any]) -> Selectors:
        """
        Extract selector strategies from element data.
        
        Args:
            element_data: Raw element data from JavaScript
            
        Returns:
            Selectors instance with multiple strategies
        """
        selectors_data = element_data.get("selectors", {})
        
        return Selectors(
            css=selectors_data.get("css"),
            xpath=selectors_data.get("xpath"),
            text=selectors_data.get("text"),
            accessibility=selectors_data.get("accessibility"),
            test_id=selectors_data.get("test_id")
        )
    
    async def build_from_handle(
        self, 
        page: Page, 
        element_handle: ElementHandle
    ) -> tuple[ElementSnapshot, Selectors]:
        """
        Build snapshot and selectors from a Playwright ElementHandle.
        
        This method evaluates JavaScript in the browser context to
        extract comprehensive element data.
        
        Args:
            page: Playwright Page instance
            element_handle: Handle to the DOM element
            
        Returns:
            Tuple of (ElementSnapshot, Selectors)
        """
        element_data = await page.evaluate("""
            (element) => {
                const rect = element.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(element);
                
                // Get all attributes
                const attributes = {};
                for (const attr of element.attributes || []) {
                    attributes[attr.name] = attr.value;
                }
                
                // Get accessible role
                let role = element.getAttribute('role');
                if (!role) {
                    const tagRoles = {
                        'button': 'button',
                        'a': 'link',
                        'input': element.type === 'checkbox' ? 'checkbox' : 
                                 element.type === 'radio' ? 'radio' :
                                 element.type === 'submit' ? 'button' : 'textbox',
                        'select': 'combobox',
                        'textarea': 'textbox',
                        'div': null, 'span': null
                    };
                    role = tagRoles[element.tagName.toLowerCase()] || null;
                }
                
                // Get text content (visible)
                let text = '';
                // Simple innerText approximation for element and children
                text = element.innerText || element.textContent || '';
                text = text.trim();
                
                // Calculate index among siblings of same type/role
                let index = 0; // 0-indexed for internal logic, but usually 1-indexed for XPath
                let sibling = element.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName === element.tagName) {
                        index++;
                    }
                    sibling = sibling.previousElementSibling;
                }
                
                // Get Label (explicit or implicit)
                let labelText = null;
                if (element.id) {
                    // Look for <label for="id">
                    const labelEl = document.querySelector(`label[for="${CSS.escape(element.id)}"]`);
                    if (labelEl) labelText = labelEl.innerText;
                }
                if (!labelText) {
                    // Look for parent label
                    const parentLabel = element.closest('label');
                    if (parentLabel) {
                         // clone to remove input's own text if nested?
                         // for now, just take parent text
                         labelText = parentLabel.innerText;
                    }
                }
                // Fallback to aria-label
                if (!labelText) {
                    labelText = element.getAttribute('aria-label');
                }
                
                // Semantic Text (List)
                // 1. Visible Text
                // 2. Title attribute
                // 3. Placeholder
                // 4. Aria-label
                // 5. Ancestor text (up to 2 levels) if short
                const semanticText = [];
                if (text && text.length < 100) semanticText.push(text);
                if (element.title) semanticText.push(element.title);
                if (element.placeholder) semanticText.push(element.placeholder);
                if (element.getAttribute('aria-label')) semanticText.push(element.getAttribute('aria-label'));
                if (labelText && labelText !== text) semanticText.push(labelText);
                
                // Ancestor text hints (closer ancestors first)
                let current = element.parentElement;
                let depth = 0;
                while (current && depth < 2) {
                    // Only identifying text, e.g. from headings or list items
                   if (['li', 'tr', 'h1', 'h2', 'h3', 'h4', 'div'].includes(current.tagName.toLowerCase())) {
                       const parentText = current.innerText || '';
                       const cleanParentText = parentText.split('\\n')[0].trim(); // First line
                       if (cleanParentText && cleanParentText.length > 0 && cleanParentText.length < 50 && !semanticText.includes(cleanParentText)) {
                           semanticText.push(cleanParentText);
                       }
                   }
                   current = current.parentElement;
                   depth++;
                }

                // Generate selectors
                function getCssSelector(el) {
                    if (el.id) return '#' + CSS.escape(el.id);
                    let selector = el.tagName.toLowerCase();
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/).filter(c => c);
                        if (classes.length > 0) {
                            selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                        }
                    }
                    return selector;
                }
                
                function getFullCssPath(el) {
                    const parts = [];
                    let current = el;
                    while (current && current !== document.body) {
                        parts.unshift(getCssSelector(current));
                        current = current.parentElement;
                    }
                    return parts.join(' > ');
                }
                
                function getXPath(el) {
                    if (el.id) return '//*[@id="' + el.id + '"]';
                    const parts = [];
                    let current = el;
                    while (current && current.nodeType === Node.ELEMENT_NODE) {
                        let idx = 1;
                        let sib = current.previousElementSibling;
                        while (sib) {
                            if (sib.tagName === current.tagName) idx++;
                            sib = sib.previousElementSibling;
                        }
                        parts.unshift(current.tagName.toLowerCase() + '[' + idx + ']');
                        current = current.parentElement;
                    }
                    return '/' + parts.join('/');
                }
                
                return {
                    tag: element.tagName.toLowerCase(),
                    text: text || null,
                    normalized_text: text ? text.toLowerCase().replace(/\\s+/g, ' ').trim() : null,
                    role: role,
                    aria_label: element.getAttribute('aria-label'),
                    attributes: attributes,
                    bounding_box: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    is_visible: computedStyle.display !== 'none' && 
                                computedStyle.visibility !== 'hidden' &&
                                rect.width > 0 && rect.height > 0,
                    is_enabled: !element.disabled,
                    selectors: {
                        css: getFullCssPath(element),
                        xpath: getXPath(element),
                        text: text ? 'text=' + text : null,
                        accessibility: role && (element.getAttribute('aria-label') || text) ?
                            role + '[name="' + (element.getAttribute('aria-label') || text) + '"]' : null,
                        test_id: element.getAttribute('data-testid') || 
                                 element.getAttribute('data-test-id') ||
                                 element.getAttribute('data-cy') || null
                    },
                    // Extra fields for Target model construction
                    extra_index: index,
                    extra_label: labelText,
                    extra_semantic_text: semanticText,
                    extra_attributes: {
                        type: element.type || null,
                        name: element.name || null,
                        placeholder: element.placeholder || null,
                        href: element.getAttribute('href') || null,
                        role: role
                    }
                };
            }
        """, element_handle)
        
        snapshot = self.build_from_data(element_data)
        selectors = self.extract_selectors(element_data)
        
        return snapshot, selectors
