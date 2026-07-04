"""
State Diff Engine for Axiome Recording Engine.

Compares two state snapshots to detect UI changes.
All comparison is deterministic based on structural properties.
"""

from ..models import StateSnapshot, ObservedChanges


class StateDiffEngine:
    """
    Computes differences between two state snapshots.
    
    Detects:
    - URL/title changes
    - Region additions/removals
    - Modal open/close events
    - Form validity changes
    - Alert additions/removals
    - Interaction count changes
    """
    
    def compute_diff(
        self,
        before: StateSnapshot,
        after: StateSnapshot
    ) -> ObservedChanges:
        """
        Compute the observed changes between two states.
        
        Args:
            before: State snapshot before interaction
            after: State snapshot after interaction
            
        Returns:
            ObservedChanges detailing all differences
        """
        # URL change
        url_changed = before.page_identity.url != after.page_identity.url
        
        # Title change
        title_changed = before.page_identity.title != after.page_identity.title
        
        # Region changes
        before_region_keys = {self._region_key(r) for r in before.ui_regions}
        after_region_keys = {self._region_key(r) for r in after.ui_regions}
        
        new_regions = [
            r.region_id for r in after.ui_regions
            if self._region_key(r) not in before_region_keys
        ]
        removed_regions = [
            r.region_id for r in before.ui_regions
            if self._region_key(r) not in after_region_keys
        ]
        
        # Modal changes
        modal_opened = (
            not before.modal_state.has_modal and 
            after.modal_state.has_modal
        )
        modal_closed = (
            before.modal_state.has_modal and 
            not after.modal_state.has_modal
        )
        
        # Form validity changes
        form_validity_changed = self._check_form_validity_changed(before, after)
        form_fields_changed = self._check_form_fields_changed(before, after)
        
        # Alert changes
        before_alerts = {a.text for a in before.alerts}
        after_alerts = {a.text for a in after.alerts}
        
        alerts_added = list(after_alerts - before_alerts)
        alerts_removed = list(before_alerts - after_alerts)
        
        # Interaction count delta
        before_count = (
            before.interaction_summary.clickable_count +
            before.interaction_summary.input_count +
            before.interaction_summary.select_count
        )
        after_count = (
            after.interaction_summary.clickable_count +
            after.interaction_summary.input_count +
            after.interaction_summary.select_count
        )
        interaction_count_delta = after_count - before_count
        
        return ObservedChanges(
            url_changed=url_changed,
            title_changed=title_changed,
            new_regions=new_regions,
            removed_regions=removed_regions,
            modal_opened=modal_opened,
            modal_closed=modal_closed,
            form_validity_changed=form_validity_changed,
            form_fields_changed=form_fields_changed,
            alerts_added=alerts_added,
            alerts_removed=alerts_removed,
            interaction_count_delta=interaction_count_delta
        )
    
    def _region_key(self, region) -> str:
        """Create a stable key for region comparison."""
        return f"{region.region_type}:{region.xpath or region.label or region.role}"
    
    def _check_form_validity_changed(
        self,
        before: StateSnapshot,
        after: StateSnapshot
    ) -> bool:
        """Check if any form validity state changed."""
        before_validity = {
            f.xpath or f.form_id: f.validity_state
            for f in before.forms
        }
        after_validity = {
            f.xpath or f.form_id: f.validity_state
            for f in after.forms
        }
        
        for key in set(before_validity.keys()) & set(after_validity.keys()):
            if before_validity[key] != after_validity[key]:
                return True
        
        return False
    
    def _check_form_fields_changed(
        self,
        before: StateSnapshot,
        after: StateSnapshot
    ) -> bool:
        """Check if form field counts changed."""
        before_counts = {f.xpath or f.form_id: f.field_count for f in before.forms}
        after_counts = {f.xpath or f.form_id: f.field_count for f in after.forms}
        
        for key in set(before_counts.keys()) & set(after_counts.keys()):
            if before_counts[key] != after_counts[key]:
                return True
        
        return False
