"""
State Snapshot Builder for Axiome Recording Engine.

Captures deterministic page state including UI regions, forms,
modals, alerts, and navigation structure using DOM inspection.
"""

from typing import Any, Optional
from urllib.parse import urlparse

from playwright.async_api import Page

from ..models import (
    StateSnapshot,
    PageIdentity,
    UIRegion,
    FormState,
    ModalState,
    AlertInfo,
    InteractionSummary,
    NavigationStructure,
)


class StateSnapshotBuilder:
    """
    Builds comprehensive page state snapshots.
    
    Uses deterministic DOM inspection and accessibility tree
    analysis to capture UI state without heuristic inference.
    
    Detection Rules:
    - UI Regions: tag/role-based detection
    - Forms: <form> elements with field analysis
    - Modals: role=dialog elements
    - Alerts: role=alert/status or alert-class patterns
    - Navigation: <nav> and role=navigation elements
    """
    
    # Alert class patterns (deterministic matching)
    ALERT_CLASS_PATTERNS = frozenset({
        "alert", "error", "success", "warning", "info",
        "toast", "notification", "message", "feedback"
    })
    
    async def build(self, page: Page) -> StateSnapshot:
        """
        Build a complete state snapshot from the current page.
        
        Args:
            page: Playwright Page instance
            
        Returns:
            StateSnapshot with all detected UI state
        """
        # Capture page identity
        page_identity = await self._capture_page_identity(page)
        
        # Capture all state components in parallel via single evaluate
        state_data = await page.evaluate("""
            () => {
                // Helper to get XPath
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
                
                // Detect UI regions
                const regions = [];
                
                // Forms
                document.querySelectorAll('form').forEach(el => {
                    regions.push({
                        region_type: 'form',
                        role: el.getAttribute('role') || 'form',
                        label: el.getAttribute('aria-label') || el.getAttribute('name') || null,
                        visible: el.offsetParent !== null,
                        xpath: getXPath(el)
                    });
                });
                
                // Dialogs/Modals
                document.querySelectorAll('[role="dialog"], [role="alertdialog"], dialog').forEach(el => {
                    regions.push({
                        region_type: 'dialog',
                        role: el.getAttribute('role') || 'dialog',
                        label: el.getAttribute('aria-label') || null,
                        visible: el.offsetParent !== null || el.open === true,
                        xpath: getXPath(el)
                    });
                });
                
                // Navigation regions
                document.querySelectorAll('nav, [role="navigation"]').forEach(el => {
                    regions.push({
                        region_type: 'navigation',
                        role: el.getAttribute('role') || 'navigation',
                        label: el.getAttribute('aria-label') || null,
                        visible: el.offsetParent !== null,
                        xpath: getXPath(el)
                    });
                });
                
                // Main content
                document.querySelectorAll('main, [role="main"]').forEach(el => {
                    regions.push({
                        region_type: 'content',
                        role: el.getAttribute('role') || 'main',
                        label: el.getAttribute('aria-label') || null,
                        visible: el.offsetParent !== null,
                        xpath: getXPath(el)
                    });
                });
                
                // Detect forms with details
                const forms = [];
                document.querySelectorAll('form').forEach(form => {
                    const inputs = form.querySelectorAll('input, textarea, select');
                    const requiredFields = [];
                    inputs.forEach(input => {
                        if (input.required || input.getAttribute('aria-required') === 'true') {
                            requiredFields.push(input.name || input.id || input.type);
                        }
                    });
                    
                    const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                    
                    let validity = 'unknown';
                    try {
                        if (form.checkValidity) {
                            validity = form.checkValidity() ? 'valid' : 'invalid';
                        }
                    } catch(e) {}
                    
                    forms.push({
                        xpath: getXPath(form),
                        field_count: inputs.length,
                        required_fields: requiredFields,
                        submit_present: submitBtn !== null,
                        validity_state: validity
                    });
                });
                
                // Detect modals
                const modalElements = document.querySelectorAll('[role="dialog"], [role="alertdialog"], dialog[open]');
                const modalRoles = [];
                let hasModal = false;
                modalElements.forEach(el => {
                    if (el.offsetParent !== null || el.open === true) {
                        hasModal = true;
                        modalRoles.push(el.getAttribute('role') || 'dialog');
                    }
                });
                
                // Detect alerts
                const alerts = [];
                const alertPatterns = ['alert', 'error', 'success', 'warning', 'info', 'toast', 'notification'];
                document.querySelectorAll('[role="alert"], [role="status"]').forEach(el => {
                    const text = el.textContent?.trim();
                    if (text) {
                        const classes = el.className.toLowerCase();
                        let type = 'info';
                        if (classes.includes('error') || classes.includes('danger')) type = 'error';
                        else if (classes.includes('success')) type = 'success';
                        else if (classes.includes('warning')) type = 'warning';
                        
                        alerts.push({type, text: text.substring(0, 200), xpath: getXPath(el)});
                    }
                });
                
                // Also check class-based alerts
                alertPatterns.forEach(pattern => {
                    document.querySelectorAll('[class*="' + pattern + '"]').forEach(el => {
                        if (el.getAttribute('role') === 'alert' || el.getAttribute('role') === 'status') return;
                        const text = el.textContent?.trim();
                        if (text && text.length < 300 && el.offsetParent !== null) {
                            let type = 'info';
                            const classes = el.className.toLowerCase();
                            if (classes.includes('error') || classes.includes('danger')) type = 'error';
                            else if (classes.includes('success')) type = 'success';
                            else if (classes.includes('warning')) type = 'warning';
                            
                            // Avoid duplicates
                            const existing = alerts.find(a => a.text === text.substring(0, 200));
                            if (!existing) {
                                alerts.push({type, text: text.substring(0, 200), xpath: getXPath(el)});
                            }
                        }
                    });
                });
                
                // Interaction summary
                const clickables = document.querySelectorAll('button, a[href], [role="button"], [onclick]');
                const inputs = document.querySelectorAll('input:not([type="hidden"]), textarea');
                const selects = document.querySelectorAll('select');
                const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                const radios = document.querySelectorAll('input[type="radio"]');
                const links = document.querySelectorAll('a[href]');
                
                // Navigation structure
                const sidebar = document.querySelector('aside, [role="complementary"], .sidebar, #sidebar');
                const topNav = document.querySelector('header nav, nav:first-of-type, [role="banner"] nav');
                const breadcrumbs = document.querySelector('[aria-label*="breadcrumb"], .breadcrumb, nav[class*="breadcrumb"]');
                const footerNav = document.querySelector('footer nav, [role="contentinfo"] nav');
                
                return {
                    regions,
                    forms,
                    modal_state: {
                        has_modal: hasModal,
                        modal_roles: modalRoles
                    },
                    alerts,
                    interaction_summary: {
                        clickable_count: clickables.length,
                        input_count: inputs.length,
                        select_count: selects.length,
                        checkbox_count: checkboxes.length,
                        radio_count: radios.length,
                        link_count: links.length
                    },
                    navigation_structure: {
                        sidebar_present: sidebar !== null,
                        top_nav_present: topNav !== null,
                        breadcrumbs_present: breadcrumbs !== null,
                        footer_nav_present: footerNav !== null
                    }
                };
            }
        """)
        
        # Build UI regions
        ui_regions = [
            UIRegion(
                region_type=r["region_type"],
                role=r["role"],
                label=r["label"],
                visible=r["visible"],
                xpath=r["xpath"]
            )
            for r in state_data.get("regions", [])
        ]
        
        # Build form states
        forms = [
            FormState(
                xpath=f["xpath"],
                field_count=f["field_count"],
                required_fields=f["required_fields"],
                submit_present=f["submit_present"],
                validity_state=f["validity_state"]
            )
            for f in state_data.get("forms", [])
        ]
        
        # Build modal state
        modal_data = state_data.get("modal_state", {})
        modal_state = ModalState(
            has_modal=modal_data.get("has_modal", False),
            modal_roles=modal_data.get("modal_roles", [])
        )
        
        # Build alerts
        alerts = [
            AlertInfo(
                type=a["type"],
                text=a["text"],
                xpath=a.get("xpath")
            )
            for a in state_data.get("alerts", [])
        ]
        
        # Build interaction summary
        summary_data = state_data.get("interaction_summary", {})
        interaction_summary = InteractionSummary(
            clickable_count=summary_data.get("clickable_count", 0),
            input_count=summary_data.get("input_count", 0),
            select_count=summary_data.get("select_count", 0),
            checkbox_count=summary_data.get("checkbox_count", 0),
            radio_count=summary_data.get("radio_count", 0),
            link_count=summary_data.get("link_count", 0)
        )
        
        # Build navigation structure
        nav_data = state_data.get("navigation_structure", {})
        navigation_structure = NavigationStructure(
            sidebar_present=nav_data.get("sidebar_present", False),
            top_nav_present=nav_data.get("top_nav_present", False),
            breadcrumbs_present=nav_data.get("breadcrumbs_present", False),
            footer_nav_present=nav_data.get("footer_nav_present", False)
        )
        
        return StateSnapshot(
            page_identity=page_identity,
            ui_regions=ui_regions,
            forms=forms,
            modal_state=modal_state,
            alerts=alerts,
            interaction_summary=interaction_summary,
            navigation_structure=navigation_structure
        )
    
    async def _capture_page_identity(self, page: Page) -> PageIdentity:
        """Capture page URL and title information."""
        url = page.url
        parsed = urlparse(url)
        title = await page.title()
        
        return PageIdentity(
            url=url,
            url_path=parsed.path or "/",
            domain=parsed.netloc,
            title=title or ""
        )
