"""
DOM Snapshot Builder for Axiome Recording Engine.

Captures full DOM tree structure for diff computation.
"""

from typing import Optional
import uuid

from playwright.async_api import Page

from ..models import DOMSnapshot, DOMNode, RecorderConfig, DEFAULT_CONFIG


class DOMSnapshotBuilder:
    """
    Builds complete DOM tree snapshots.
    
    Captures:
    - Element hierarchy with stable XPaths
    - Attributes and text content
    - ARIA roles and accessibility info
    - Visibility state
    
    Performance optimizations:
    - Maximum depth limiting
    - Maximum node count limiting
    - Exclusion of script/style elements
    """
    
    def __init__(self, config: Optional[RecorderConfig] = None):
        """
        Initialize the DOM snapshot builder.
        
        Args:
            config: Optional recorder configuration
        """
        self._config = config or DEFAULT_CONFIG
    
    async def build(self, page: Page) -> DOMSnapshot:
        """
        Build a DOM snapshot from the current page.
        
        Args:
            page: Playwright Page instance
            
        Returns:
            DOMSnapshot with all captured nodes
        """
        max_depth = self._config.dom_max_depth
        max_nodes = self._config.dom_max_nodes
        exclude_hidden = self._config.exclude_hidden_elements
        exclude_scripts = self._config.exclude_script_style
        
        # Extract DOM tree via JavaScript
        dom_data = await page.evaluate("""
            ({maxDepth, maxNodes, excludeHidden, excludeScripts}) => {
                const nodes = [];
                let nodeCount = 0;
                
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
                
                function isVisible(el) {
                    try {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden';
                    } catch(e) {
                        return true;
                    }
                }
                
                function processNode(el, depth, parentId) {
                    if (nodeCount >= maxNodes || depth > maxDepth) return null;
                    
                    const tag = el.tagName.toLowerCase();
                    
                    // Skip script/style if configured
                    if (excludeScripts && (tag === 'script' || tag === 'style' || tag === 'noscript')) {
                        return null;
                    }
                    
                    const visible = isVisible(el);
                    
                    // Skip hidden if configured
                    if (excludeHidden && !visible && depth > 1) {
                        return null;
                    }
                    
                    nodeCount++;
                    const nodeId = 'node_' + nodeCount;
                    
                    // Get attributes (limited set for performance)
                    const attrs = {};
                    const importantAttrs = ['id', 'class', 'name', 'type', 'role', 
                                           'aria-label', 'data-testid', 'href', 'src'];
                    importantAttrs.forEach(attr => {
                        const val = el.getAttribute(attr);
                        if (val) attrs[attr] = val.substring(0, 200);
                    });
                    
                    // Get direct text content
                    let text = '';
                    for (const child of el.childNodes) {
                        if (child.nodeType === Node.TEXT_NODE) {
                            text += child.textContent;
                        }
                    }
                    text = text.trim().substring(0, 200) || null;
                    
                    // Process children
                    const childrenIds = [];
                    for (const child of el.children) {
                        const childResult = processNode(child, depth + 1, nodeId);
                        if (childResult) {
                            childrenIds.push(childResult);
                        }
                    }
                    
                    nodes.push({
                        node_id: nodeId,
                        xpath: getXPath(el),
                        tag: tag,
                        attributes: attrs,
                        text: text,
                        role: el.getAttribute('role'),
                        visible: visible,
                        children_ids: childrenIds,
                        parent_id: parentId,
                        depth: depth
                    });
                    
                    return nodeId;
                }
                
                // Start from body
                const rootId = processNode(document.body, 0, null);
                
                return {
                    nodes: nodes,
                    root_id: rootId,
                    node_count: nodeCount,
                    max_depth: Math.max(...nodes.map(n => n.depth), 0)
                };
            }
        """, {
            "maxDepth": max_depth,
            "maxNodes": max_nodes,
            "excludeHidden": exclude_hidden,
            "excludeScripts": exclude_scripts
        })
        
        # Build DOMNode objects
        nodes = [
            DOMNode(
                node_id=n["node_id"],
                xpath=n["xpath"],
                tag=n["tag"],
                attributes=n.get("attributes", {}),
                text=n.get("text"),
                role=n.get("role"),
                visible=n.get("visible", True),
                children_ids=n.get("children_ids", []),
                parent_id=n.get("parent_id"),
                depth=n.get("depth", 0)
            )
            for n in dom_data.get("nodes", [])
        ]
        
        return DOMSnapshot(
            url=page.url,
            nodes=nodes,
            root_id=dom_data.get("root_id"),
            node_count=dom_data.get("node_count", len(nodes)),
            max_depth=dom_data.get("max_depth", 0)
        )
