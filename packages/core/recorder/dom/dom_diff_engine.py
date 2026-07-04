"""
DOM Diff Engine for Axiome Recording Engine.

Computes structural differences between two DOM snapshots.
"""

from typing import Optional

from ..models import (
    DOMSnapshot,
    DOMDiff,
    DOMNodeChange,
    TextChange,
    AttributeChange,
)


class DOMDiffEngine:
    """
    Computes differences between DOM snapshots.
    
    Uses XPath as stable node identity for comparison.
    
    Detects:
    - Added nodes (new XPaths)
    - Removed nodes (missing XPaths)
    - Modified nodes (same XPath, different structure)
    - Text changes
    - Attribute changes
    """
    
    def compute_diff(
        self,
        before: DOMSnapshot,
        after: DOMSnapshot
    ) -> DOMDiff:
        """
        Compute differences between two DOM snapshots.
        
        Args:
            before: DOM snapshot before interaction
            after: DOM snapshot after interaction
            
        Returns:
            DOMDiff with all detected changes
        """
        # Build XPath maps
        before_nodes = {n.xpath: n for n in before.nodes}
        after_nodes = {n.xpath: n for n in after.nodes}
        
        before_xpaths = set(before_nodes.keys())
        after_xpaths = set(after_nodes.keys())
        
        # Find added nodes
        added_xpaths = after_xpaths - before_xpaths
        added_nodes = [
            DOMNodeChange(
                xpath=xpath,
                tag=after_nodes[xpath].tag,
                change_type="added",
                details=f"New {after_nodes[xpath].tag} element"
            )
            for xpath in added_xpaths
        ]
        
        # Find removed nodes
        removed_xpaths = before_xpaths - after_xpaths
        removed_nodes = [
            DOMNodeChange(
                xpath=xpath,
                tag=before_nodes[xpath].tag,
                change_type="removed",
                details=f"Removed {before_nodes[xpath].tag} element"
            )
            for xpath in removed_xpaths
        ]
        
        # Find modified nodes (same xpath but different content)
        modified_nodes = []
        text_changes = []
        attribute_changes = []
        
        common_xpaths = before_xpaths & after_xpaths
        for xpath in common_xpaths:
            before_node = before_nodes[xpath]
            after_node = after_nodes[xpath]
            
            # Check for structural changes
            if before_node.tag != after_node.tag:
                modified_nodes.append(DOMNodeChange(
                    xpath=xpath,
                    tag=after_node.tag,
                    change_type="modified",
                    details=f"Tag changed: {before_node.tag} -> {after_node.tag}"
                ))
                continue
            
            # Check for text changes
            if before_node.text != after_node.text:
                text_changes.append(TextChange(
                    xpath=xpath,
                    before=before_node.text,
                    after=after_node.text
                ))
            
            # Check for attribute changes
            before_attrs = before_node.attributes
            after_attrs = after_node.attributes
            
            all_attr_keys = set(before_attrs.keys()) | set(after_attrs.keys())
            for attr in all_attr_keys:
                before_val = before_attrs.get(attr)
                after_val = after_attrs.get(attr)
                
                if before_val != after_val:
                    # Skip class changes that are just ordering differences
                    if attr == "class" and before_val and after_val:
                        before_classes = set(before_val.split())
                        after_classes = set(after_val.split())
                        if before_classes == after_classes:
                            continue
                    
                    attribute_changes.append(AttributeChange(
                        xpath=xpath,
                        attribute=attr,
                        before=before_val,
                        after=after_val
                    ))
        
        return DOMDiff(
            before_snapshot_id=before.snapshot_id,
            after_snapshot_id=after.snapshot_id,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            modified_nodes=modified_nodes,
            text_changes=text_changes,
            attribute_changes=attribute_changes
        )
