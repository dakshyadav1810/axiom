"""
Semantic Page Classifier for Axiome Recording Engine.

Rule-based page classification using structural signals.
All classification is deterministic without AI inference.
"""

from typing import Optional

from ..models import StateSnapshot, SemanticPageLabels


class SemanticPageClassifier:
    """
    Classifies pages using deterministic structural rules.
    
    Supported Labels:
    - authentication_screen: Login/signup forms
    - dashboard_screen: Dashboard layouts with sidebar
    - listing_screen: Tables or repeated grid items
    - navigation_shell: Primary navigation with minimal content
    - content_screen: Main content without form focus
    - settings_screen: Settings/preferences forms
    - search_screen: Search-focused pages
    - error_screen: Error pages (404, 500, etc.)
    """
    
    def classify(self, state: StateSnapshot) -> SemanticPageLabels:
        """
        Classify the page based on current state.
        
        Args:
            state: Current page state snapshot
            
        Returns:
            SemanticPageLabels with matched labels and rules
        """
        labels = []
        scores = {}
        applied_rules = []
        
        # Rule 1: Authentication Screen
        auth_score = self._check_authentication_screen(state)
        if auth_score > 0.6:
            labels.append("authentication_screen")
            scores["authentication_screen"] = auth_score
            applied_rules.append("auth_form_with_password")
        
        # Rule 2: Dashboard Screen
        dash_score = self._check_dashboard_screen(state)
        if dash_score > 0.6:
            labels.append("dashboard_screen")
            scores["dashboard_screen"] = dash_score
            applied_rules.append("sidebar_with_content_regions")
        
        # Rule 3: Listing Screen
        listing_score = self._check_listing_screen(state)
        if listing_score > 0.6:
            labels.append("listing_screen")
            scores["listing_screen"] = listing_score
            applied_rules.append("table_or_grid_layout")
        
        # Rule 4: Navigation Shell
        nav_score = self._check_navigation_shell(state)
        if nav_score > 0.6:
            labels.append("navigation_shell")
            scores["navigation_shell"] = nav_score
            applied_rules.append("nav_dominant_layout")
        
        # Rule 5: Content Screen
        content_score = self._check_content_screen(state)
        if content_score > 0.5 and "authentication_screen" not in labels:
            labels.append("content_screen")
            scores["content_screen"] = content_score
            applied_rules.append("main_content_present")
        
        # Rule 6: Settings Screen
        settings_score = self._check_settings_screen(state)
        if settings_score > 0.6:
            labels.append("settings_screen")
            scores["settings_screen"] = settings_score
            applied_rules.append("settings_form_pattern")
        
        # Rule 7: Search Screen
        search_score = self._check_search_screen(state)
        if search_score > 0.6:
            labels.append("search_screen")
            scores["search_screen"] = search_score
            applied_rules.append("search_input_dominant")
        
        # Rule 8: Error Screen
        error_score = self._check_error_screen(state)
        if error_score > 0.7:
            labels.append("error_screen")
            scores["error_screen"] = error_score
            applied_rules.append("error_page_indicators")
        
        return SemanticPageLabels(
            labels=labels,
            confidence_scores=scores,
            applied_rules=applied_rules
        )
    
    def _check_authentication_screen(self, state: StateSnapshot) -> float:
        """
        Check for authentication/login page pattern.
        
        Rules:
        - Has form with password input
        - Has submit button
        - URL or title contains auth keywords
        """
        score = 0.0
        
        # Check for password field in forms
        has_password_form = False
        for form in state.forms:
            if any("password" in f.lower() for f in form.required_fields):
                has_password_form = True
                score += 0.4
                if form.submit_present:
                    score += 0.2
        
        # Check URL/title for auth keywords
        auth_keywords = {"login", "signin", "sign-in", "signup", "sign-up", 
                        "register", "auth", "password", "forgot"}
        
        url_path = state.page_identity.url_path.lower()
        title = state.page_identity.title.lower()
        
        if any(kw in url_path or kw in title for kw in auth_keywords):
            score += 0.3
        
        # Minimal navigation suggests auth page
        if not state.navigation_structure.sidebar_present:
            score += 0.1
        
        return min(score, 1.0)
    
    def _check_dashboard_screen(self, state: StateSnapshot) -> float:
        """
        Check for dashboard layout pattern.
        
        Rules:
        - Sidebar navigation present
        - Multiple content regions
        - No password inputs
        """
        score = 0.0
        
        if state.navigation_structure.sidebar_present:
            score += 0.4
        
        # Multiple content regions
        content_regions = [r for r in state.ui_regions if r.region_type == "content"]
        if len(content_regions) >= 1:
            score += 0.2
        
        # Top nav also present
        if state.navigation_structure.top_nav_present:
            score += 0.2
        
        # No password inputs (not auth page)
        has_password = any(
            "password" in f.lower() 
            for form in state.forms 
            for f in form.required_fields
        )
        if not has_password:
            score += 0.2
        
        # Dashboard keywords in URL
        dash_keywords = {"dashboard", "home", "overview", "main", "portal"}
        if any(kw in state.page_identity.url_path.lower() for kw in dash_keywords):
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_listing_screen(self, state: StateSnapshot) -> float:
        """
        Check for listing/table page pattern.
        
        Rules:
        - Contains table or grid layout
        - Multiple repeated items
        - URL contains list keywords
        """
        score = 0.0
        
        # Check for listing regions
        listing_regions = [r for r in state.ui_regions if r.region_type == "listing"]
        if listing_regions:
            score += 0.5
        
        # Listing keywords in URL
        list_keywords = {"list", "table", "items", "records", "data", "all", "browse"}
        if any(kw in state.page_identity.url_path.lower() for kw in list_keywords):
            score += 0.3
        
        # Many links suggests listing
        if state.interaction_summary.link_count > 10:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_navigation_shell(self, state: StateSnapshot) -> float:
        """
        Check for navigation-dominant layout.
        
        Rules:
        - Nav or sidebar present
        - Minimal content regions
        """
        score = 0.0
        
        nav_regions = [r for r in state.ui_regions if r.region_type == "navigation"]
        content_regions = [r for r in state.ui_regions if r.region_type == "content"]
        
        # Navigation dominant
        if len(nav_regions) > len(content_regions):
            score += 0.5
        
        if state.navigation_structure.sidebar_present or state.navigation_structure.top_nav_present:
            score += 0.3
        
        # Few forms
        if len(state.forms) == 0:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_content_screen(self, state: StateSnapshot) -> float:
        """
        Check for content-focused page.
        
        Rules:
        - Main content region present
        - Not form-focused
        """
        score = 0.0
        
        content_regions = [r for r in state.ui_regions if r.region_type == "content"]
        if content_regions:
            score += 0.5
        
        # Not heavily form-focused
        if len(state.forms) <= 1:
            score += 0.3
        
        # Some text content (links count as content)
        if state.interaction_summary.link_count > 3:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_settings_screen(self, state: StateSnapshot) -> float:
        """
        Check for settings/preferences page.
        
        Rules:
        - Form present
        - URL contains settings keywords
        - Multiple input fields
        """
        score = 0.0
        
        settings_keywords = {"settings", "preferences", "config", "profile", "account"}
        if any(kw in state.page_identity.url_path.lower() for kw in settings_keywords):
            score += 0.5
        
        if any(kw in state.page_identity.title.lower() for kw in settings_keywords):
            score += 0.2
        
        # Has form with multiple fields
        for form in state.forms:
            if form.field_count > 3:
                score += 0.3
                break
        
        return min(score, 1.0)
    
    def _check_search_screen(self, state: StateSnapshot) -> float:
        """
        Check for search-focused page.
        
        Rules:
        - Search input present
        - URL contains search keywords
        """
        score = 0.0
        
        search_keywords = {"search", "query", "find", "results"}
        if any(kw in state.page_identity.url_path.lower() for kw in search_keywords):
            score += 0.5
        
        if any(kw in state.page_identity.title.lower() for kw in search_keywords):
            score += 0.3
        
        # Input fields present
        if state.interaction_summary.input_count > 0:
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_error_screen(self, state: StateSnapshot) -> float:
        """
        Check for error page (404, 500, etc.).
        
        Rules:
        - Error alerts present
        - URL/title contains error codes
        - Minimal navigation
        """
        score = 0.0
        
        # Error alerts
        error_alerts = [a for a in state.alerts if a.type == "error"]
        if error_alerts:
            score += 0.4
        
        # Error codes in title
        error_codes = {"404", "500", "403", "error", "not found", "server error"}
        title_lower = state.page_identity.title.lower()
        if any(code in title_lower for code in error_codes):
            score += 0.5
        
        # Minimal content
        if state.interaction_summary.link_count < 5:
            score += 0.1
        
        return min(score, 1.0)
