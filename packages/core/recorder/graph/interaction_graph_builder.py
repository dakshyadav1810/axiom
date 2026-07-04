"""
Interaction Graph Builder for Axiome Recording Engine.

Discovers all interactive elements and builds a graph
representing possible user interactions.
"""

from typing import Optional
import uuid

from playwright.async_api import Page

from ..models import (
    InteractionGraph,
    InteractionNode,
    GraphEdge,
    StateSnapshot,
    UIRegion,
)


class InteractionGraphBuilder:
    """
    Builds interaction graphs from page state.
    
    Discovers interactive elements:
    - Buttons (button, [role=button], input[type=submit])
    - Links (a[href])
    - Inputs (input, textarea)
    - Selects (select)
    - Checkboxes and radios
    
    Associates nodes with their container regions.
    """
    
    async def build(
        self,
        page: Page,
        state: Optional[StateSnapshot] = None
    ) -> InteractionGraph:
        """
        Build an interaction graph from the current page.
        
        Args:
            page: Playwright Page instance
            state: Optional state snapshot for region association
            
        Returns:
            InteractionGraph with all interactive nodes
        """
        # Extract all interactive elements via JavaScript
        nodes_data = await page.evaluate("""
            () => {
                function getXPath(el) {
                    if (!el) return '';
                    if (el.id) return '//*[@id="' + el.id + '"]';
                    
                    const parts = [];
                    let current = el;
                    while (current && current.nodeType === Node.ELEMENT_NODE) {
                        let index = 1;
                        let sibling = current.previousElementSibling;
                        while (sibling) {
                            if (sibling.tagName === current.tagName) index++;
                            sibling = sibling.previousElementSibling;
                        }
                        parts.unshift(current.tagName.toLowerCase() + '[' + index + ']');
                        current = current.parentElement;
                    }
                    return '/' + parts.join('/');
                }
                
                function getContainerXPath(el) {
                    // Find nearest semantic container
                    const containers = ['form', 'dialog', 'nav', 'main', 'section', 'article', 'aside'];
                    let current = el.parentElement;
                    while (current && current !== document.body) {
                        const tag = current.tagName.toLowerCase();
                        const role = current.getAttribute('role');
                        if (containers.includes(tag) || 
                            ['dialog', 'navigation', 'main', 'form'].includes(role)) {
                            return getXPath(current);
                        }
                        current = current.parentElement;
                    }
                    return null;
                }
                
                function isVisible(el) {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' &&
                           el.offsetParent !== null;
                }
                
                function getNodeType(el) {
                    const tag = el.tagName.toLowerCase();
                    const type = el.getAttribute('type')?.toLowerCase();
                    const role = el.getAttribute('role');
                    
                    if (tag === 'button' || role === 'button' || type === 'submit' || type === 'button') {
                        return 'button';
                    }
                    if (tag === 'a' && el.hasAttribute('href')) {
                        return 'link';
                    }
                    if (tag === 'select') {
                        return 'select';
                    }
                    if (tag === 'textarea') {
                        return 'textarea';
                    }
                    if (tag === 'input') {
                        if (type === 'checkbox') return 'checkbox';
                        if (type === 'radio') return 'radio';
                        return 'input';
                    }
                    if (role === 'button') return 'button';
                    if (role === 'link') return 'link';
                    if (role === 'checkbox') return 'checkbox';
                    if (role === 'radio') return 'radio';
                    
                    return 'button';  // Default for clickable
                }
                
                const nodes = [];
                const selectors = [
                    'button',
                    'a[href]',
                    'input:not([type="hidden"])',
                    'textarea',
                    'select',
                    '[role="button"]',
                    '[role="link"]',
                    '[role="checkbox"]',
                    '[role="radio"]',
                    '[tabindex]:not([tabindex="-1"])'
                ];
                
                const seen = new Set();
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        const xpath = getXPath(el);
                        if (seen.has(xpath)) return;
                        seen.add(xpath);
                        
                        const text = el.textContent?.trim()?.substring(0, 100) || 
                                    el.getAttribute('aria-label') ||
                                    el.getAttribute('placeholder') ||
                                    el.getAttribute('value') ||
                                    el.getAttribute('title') || '';
                        
                        nodes.push({
                            node_type: getNodeType(el),
                            text: text || null,
                            role: el.getAttribute('role'),
                            aria_label: el.getAttribute('aria-label'),
                            visible: isVisible(el),
                            enabled: !el.disabled,
                            xpath: xpath,
                            container_xpath: getContainerXPath(el),
                            attributes: {
                                id: el.id || null,
                                name: el.getAttribute('name'),
                                type: el.getAttribute('type'),
                                href: el.getAttribute('href'),
                                class: el.className?.substring?.(0, 100) || null
                            }
                        });
                    });
                });
                
                return nodes;
            }
        """)
        
        # Build region lookup if state provided
        region_xpath_map = {}
        if state:
            for region in state.ui_regions:
                if region.xpath:
                    region_xpath_map[region.xpath] = region.region_id
        
        # Build nodes and edges
        nodes = []
        edges = []
        
        for data in nodes_data:
            node_id = str(uuid.uuid4())
            
            # Find container region
            container_region_id = None
            container_xpath = data.get("container_xpath")
            if container_xpath and container_xpath in region_xpath_map:
                container_region_id = region_xpath_map[container_xpath]
            
            # Clean attributes
            attrs = {k: v for k, v in data.get("attributes", {}).items() if v}
            
            node = InteractionNode(
                node_id=node_id,
                node_type=data["node_type"],
                text=data.get("text"),
                role=data.get("role"),
                aria_label=data.get("aria_label"),
                visible=data.get("visible", True),
                enabled=data.get("enabled", True),
                container_region_id=container_region_id,
                xpath=data.get("xpath"),
                attributes=attrs
            )
            nodes.append(node)
            
            # Create edge if in a region
            if container_region_id:
                edge = GraphEdge(
                    parent_region_id=container_region_id,
                    child_node_id=node_id,
                    relation="contains"
                )
                edges.append(edge)
        
        return InteractionGraph(
            state_id=state.state_id if state else None,
            nodes=nodes,
            edges=edges
        )
