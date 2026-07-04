"""
Step Assembler for Axiome Recording Engine.

Combines interaction events with element snapshots and context
paths to build complete Step objects.
"""

from datetime import datetime
import asyncio
import hashlib
from typing import Any, Optional
import uuid

from playwright.async_api import Page

from ..models import (
    Step,
    Target,
    RecordedContext,
    Resolution,
    StepStateMarkers,
    DOMExistenceCheck,
    ActionType,
    GeneralizationLevel,
    PreferredStrategy,
)
from .element_snapshot_builder import ElementSnapshotBuilder
from .context_path_builder import ContextPathBuilder
from .interaction_observer import InteractionEvent


GENERIC_SEMANTIC_TOKENS = {
    "a", "button", "link", "input", "select", "textarea",
    "div", "span", "img", "svg", "icon", "element",
}

INTENT_KEYWORDS = {
    "delete": ("delete", "remove", "trash", "discard", "x"),
    "edit": ("edit", "update", "modify", "rename"),
    "checkout": ("checkout", "pay", "payment", "purchase", "buy"),
    "create": ("create", "add", "new", "invite"),
    "submit": ("submit", "save", "confirm", "done"),
    "search": ("search", "filter", "find"),
    "view": ("view", "details", "open", "see"),
}


def _is_weak_semantic_token(value: Optional[str]) -> bool:
    if not value:
        return True
    normalized = " ".join(str(value).strip().lower().split())
    if not normalized:
        return True
    if normalized in GENERIC_SEMANTIC_TOKENS:
        return True
    if len(normalized) <= 1:
        return True
    return False


class StepAssembler:
    """
    Assembles complete Step objects from interaction events.
    
    Combines data from the InteractionObserver, ElementSnapshotBuilder,
    and ContextPathBuilder into structured Step objects ready for
    inclusion in a Flow.
    
    Example:
        assembler = StepAssembler()
        step = await assembler.assemble(event, page)
        flow.add_step(step)
    """
    
    def __init__(self):
        """Initialize the step assembler with builders."""
        self._snapshot_builder = ElementSnapshotBuilder()
        self._context_builder = ContextPathBuilder()
    
    async def assemble(
        self,
        event: InteractionEvent,
        page: Page,
        order: int = 1
    ) -> Step:
        """
        Assemble a Step from an interaction event.
        
        Args:
            event: The captured interaction event
            page: Playwright Page for additional data extraction
            order: Step order number in the flow
            
        Returns:
            Complete Step object
        """
        # Map event type to ActionType
        action_type = self._map_action_type(event.event_type)
        
        # Build recorded context
        viewport_size = page.viewport_size or {"width": 1920, "height": 1080}
        
        # Page queries may fail if a navigation destroyed the context.
        # Fall back to safe defaults so the step is never lost.
        try:
            scroll_position = await self._get_scroll_position(page)
        except Exception:
            scroll_position = {"x": 0, "y": 0}
        
        try:
            page_title = await page.title()
        except Exception:
            page_title = ""
        
        recorded_context = RecordedContext(
            url=event.url or page.url,
            viewport_width=viewport_size["width"],
            viewport_height=viewport_size["height"],
            scroll_x=scroll_position["x"],
            scroll_y=scroll_position["y"],
            timestamp=event.timestamp,
            page_title=page_title,
            context_id=event.context_id,
            opener_context_id=event.opener_context_id,
        )
        
        # Build target (None for navigate events)
        target = None
        if event.element_data and action_type not in {ActionType.NAVIGATE, ActionType.SWITCH_CONTEXT}:
            target = self._build_target(event.element_data)
        
        # Lightweight pre/post state markers for replay diagnostics
        state_markers = await self._capture_state_markers(
            page,
            target,
            event.url or page.url
        )
        
        # Determine resolution preferences based on action type
        resolution = self._determine_resolution(action_type, event.element_data)
        
        return Step(
            step_id=str(uuid.uuid4()),
            order=order,
            action=action_type,
            target=target,
            input_value=event.input_value if action_type in {ActionType.TYPE, ActionType.SELECT, ActionType.KEYPRESS, ActionType.SWITCH_CONTEXT} else None,
            resolution=resolution,
            preconditions=[],
            expected_outcome=None,
            recorded_context=recorded_context,
            state_markers=state_markers,
        )
    
    def _map_action_type(self, event_type: str) -> ActionType:
        """Map event type string to ActionType enum."""
        mapping = {
            "click": ActionType.CLICK,
            "hover": ActionType.HOVER,
            "type": ActionType.TYPE,
            "select": ActionType.SELECT,
            "submit": ActionType.SUBMIT,
            "navigate": ActionType.NAVIGATE,
            "wait": ActionType.WAIT,
            "keypress": ActionType.KEYPRESS,
            "switch_context": ActionType.SWITCH_CONTEXT,
        }
        return mapping.get(event_type, ActionType.CLICK)
    
    def _build_target(self, element_data: dict[str, Any]) -> Target:
        """Build a Target from element data."""
        # Build element snapshot
        snapshot = self._snapshot_builder.build_from_data(element_data)
        
        # Extract selectors
        selectors = self._snapshot_builder.extract_selectors(element_data)
        
        # Build context path from ancestors if available
        context_path = self._context_builder.build_from_data(element_data)
        
        # Generate friendly name
        friendly_name = snapshot.get_friendly_name()

        # Build semantic_text from available element signals
        # This is critical for the resolver's SemanticResolver to match elements
        semantic_text_items = []

        # 1. Visible text content
        if snapshot.text:
            clean = snapshot.text.strip()[:100]
            if clean:
                semantic_text_items.append(clean)

        # 2. ARIA label
        if snapshot.aria_label and snapshot.aria_label not in semantic_text_items:
            semantic_text_items.append(snapshot.aria_label)

        # 3. Associated label text (e.g. <label for="...">)
        label_text = element_data.get("label_text")
        if label_text and label_text not in semantic_text_items:
            semantic_text_items.append(label_text)

        # 4. Placeholder text (common for inputs)
        placeholder = element_data.get("attributes", {}).get("placeholder")
        if placeholder and placeholder not in semantic_text_items:
            semantic_text_items.append(placeholder)

        # 5. Title attribute
        title = element_data.get("attributes", {}).get("title")
        if title and title not in semantic_text_items:
            semantic_text_items.append(title)

        # 6. Extra semantic text from JS extraction (ancestor hints, etc.)
        # For icon-only clickable controls, ancestor text is often row/card
        # content and can cause semantic false positives during replay.
        include_ancestor_semantics = not (
            element_data.get("tag", "").lower() in {"a", "button"} and
            _is_weak_semantic_token(snapshot.text) and
            _is_weak_semantic_token(snapshot.aria_label) and
            _is_weak_semantic_token(label_text)
        )
        extra_sem = element_data.get("extra_semantic_text") or []
        if include_ancestor_semantics:
            for item in extra_sem:
                if item and not _is_weak_semantic_token(item) and item not in semantic_text_items:
                    semantic_text_items.append(item)

        # 7. Friendly name as fallback if it adds new info
        if friendly_name and not _is_weak_semantic_token(friendly_name) and friendly_name not in semantic_text_items:
            semantic_text_items.append(friendly_name)

        # ── Escalation: if get_friendly_name() still returned a generic label,
        # try to find something more descriptive from the richer signals we have.
        if _is_weak_semantic_token(friendly_name):
            # Try semantic_text_items in order — first non-weak token wins
            for candidate in semantic_text_items:
                if not _is_weak_semantic_token(candidate):
                    friendly_name = candidate[:50]
                    break

            # Try the innermost non-weak context_path node label
            if _is_weak_semantic_token(friendly_name):
                for node in context_path:
                    node_label = (
                        node.attributes.get("aria-label")
                        or node.attributes.get("title")
                        or node.role
                    )
                    if not _is_weak_semantic_token(node_label):
                        friendly_name = str(node_label)[:50]
                        break

            # Last resort: use the Generic label from get_friendly_name() as-is
            # (it is now "Button", "Link", "Text field" etc. — never a raw tag)
        
        # Extract extra semantic signals
        role = element_data.get("role")
        label = label_text or element_data.get("extra_label")
        semantic_text = semantic_text_items
        attributes = element_data.get("extra_attributes") or {}
        sibling_index = element_data.get("sibling_index")
        sibling_count = element_data.get("sibling_count", 0)
        if sibling_index is not None:
            attributes.setdefault("sibling_index", sibling_index)
        if sibling_count:
            attributes.setdefault("sibling_count", sibling_count)
        index = None
        if self._should_record_target_index(
            snapshot,
            selectors,
            element_data,
            sibling_index,
            sibling_count,
        ):
            index = sibling_index
        disambiguators = self._build_disambiguators(
            snapshot,
            element_data,
            sibling_index,
            sibling_count
        )
        action_intent = self._infer_action_intent(
            element_data.get("tag", ""),
            semantic_text_items,
            snapshot.nearby_text,
            element_data.get("attributes", {}),
        )
        
        return Target(
            friendly_name=friendly_name,
            element_snapshot=snapshot,
            selectors=selectors,
            context_path=context_path,
            role=role,
            label=label,
            semantic_text=semantic_text,
            attributes=attributes,
            index=index,
            disambiguators=disambiguators,
            action_intent=action_intent,
        )

    def _should_record_target_index(
        self,
        snapshot,
        selectors,
        element_data: dict[str, Any],
        sibling_index: Optional[int],
        sibling_count: int,
    ) -> bool:
        """Record index only when it is a real disambiguator, not a default signal."""
        if sibling_index is None or sibling_index < 0:
            return False
        if sibling_count <= 1:
            return False

        attrs = element_data.get("attributes", {}) or {}
        has_durable_anchor = bool(
            (selectors and selectors.test_id)
            or attrs.get("id")
            or attrs.get("name")
            or attrs.get("aria-label")
        )
        if has_durable_anchor:
            return False

        tag = (snapshot.tag if snapshot else element_data.get("tag", "")).lower()
        repeated_actionable_tags = {"button", "a", "input", "select", "textarea", "option", "li", "tr"}
        return tag in repeated_actionable_tags
    
    def _determine_resolution(
        self,
        action_type: ActionType,
        element_data: Optional[dict[str, Any]]
    ) -> Resolution:
        """
        Determine resolution preferences based on action and element.
        
        Uses heuristics to set appropriate matching strictness:
        - Navigation: direct_navigation strategy
        - Buttons/submit: same_element preferred
        - Text inputs: semantic_context for fields that might move
        - Elements with test IDs: minimal generalization
        """
        if action_type == ActionType.NAVIGATE:
            return Resolution(
                generalization_level=GeneralizationLevel.MINIMAL,
                preferred_strategy=PreferredStrategy.DIRECT_NAVIGATION
            )

        if action_type == ActionType.SWITCH_CONTEXT:
            return Resolution(
                generalization_level=GeneralizationLevel.MINIMAL,
                preferred_strategy=PreferredStrategy.DIRECT_NAVIGATION,
            )
        
        # Hover targets are specific UI elements (menus, dropdowns)
        if action_type == ActionType.HOVER:
            return Resolution(
                generalization_level=GeneralizationLevel.MINIMAL,
                preferred_strategy=PreferredStrategy.SAME_ELEMENT
            )
        
        if not element_data:
            return Resolution()
        
        selectors = element_data.get("selectors", {})
        attrs = element_data.get("attributes", {})
        tag = element_data.get("tag", "")
        
        # Elements with test IDs get strict matching
        if selectors.get("test_id"):
            return Resolution(
                generalization_level=GeneralizationLevel.MINIMAL,
                preferred_strategy=PreferredStrategy.SAME_ELEMENT
            )
        
        # Elements with unique IDs get strict matching
        if attrs.get("id") and not attrs["id"].startswith("react-"):
            return Resolution(
                generalization_level=GeneralizationLevel.MINIMAL,
                preferred_strategy=PreferredStrategy.SAME_ELEMENT
            )
        
        # Submit buttons prefer exact matching
        if action_type == ActionType.SUBMIT:
            return Resolution(
                generalization_level=GeneralizationLevel.MINIMAL,
                preferred_strategy=PreferredStrategy.SAME_ELEMENT
            )
        
        # Input fields use semantic context
        if tag in {"input", "textarea", "select"}:
            return Resolution(
                generalization_level=GeneralizationLevel.MODERATE,
                preferred_strategy=PreferredStrategy.SEMANTIC_CONTEXT
            )
        
        # Default moderate matching
        return Resolution(
            generalization_level=GeneralizationLevel.MODERATE,
            preferred_strategy=PreferredStrategy.SEMANTIC_CONTEXT
        )
    
    async def _get_scroll_position(self, page: Page) -> dict[str, float]:
        """Get current scroll position from page."""
        try:
            return await page.evaluate("""
                () => ({
                    x: window.scrollX || window.pageXOffset || 0,
                    y: window.scrollY || window.pageYOffset || 0
                })
            """)
        except Exception:
            return {"x": 0, "y": 0}

    def _build_disambiguators(
        self,
        snapshot,
        element_data: dict[str, Any],
        sibling_index: Optional[int],
        sibling_count: int,
    ) -> dict[str, Any]:
        """Build compact disambiguators for repeated/list structures."""
        row_identity: dict[str, Any] = {}
        for anc in element_data.get("ancestors") or []:
            attrs = anc.get("attributes") or {}
            data_attrs = {k: v for k, v in attrs.items() if k.startswith("data-") and v}
            if attrs.get("id") or data_attrs:
                row_identity = {
                    "tag": anc.get("tag"),
                    "id": attrs.get("id"),
                    "data_attrs": data_attrs,
                }
                break

        nearby_text_hash = None
        if snapshot and snapshot.nearby_text:
            nearby_text_hash = hashlib.sha1(snapshot.nearby_text.encode("utf-8")).hexdigest()[:12]

        return {
            "row_identity": row_identity,
            "nearby_text_hash": nearby_text_hash,
            "sibling_index": sibling_index if sibling_index is not None else -1,
            "sibling_count": sibling_count or 0,
        }

    def _infer_action_intent(
        self,
        tag: str,
        semantic_text: list[str],
        nearby_text: Optional[str],
        attributes: dict[str, Any],
    ) -> str:
        """Infer compact action intent from local text and attributes."""
        chunks: list[str] = []
        chunks.extend(semantic_text or [])
        if nearby_text:
            chunks.append(nearby_text)
        for key in ("class", "id", "name", "aria-label", "title"):
            if attributes.get(key):
                chunks.append(str(attributes[key]))
        haystack = " ".join(chunks).lower()

        for intent, words in INTENT_KEYWORDS.items():
            if any(word in haystack for word in words):
                return intent

        if tag.lower() in {"input", "textarea", "select"}:
            return "input"
        return "click"

    async def _capture_state_markers(
        self,
        page: Page,
        target: Optional[Target],
        fallback_url: str,
    ) -> Optional[StepStateMarkers]:
        """Capture compact pre/post URL + key selector existence checks."""
        if not target:
            return None

        selectors = self._derive_marker_selectors(target)
        if not selectors:
            return None

        pre_url = fallback_url
        try:
            pre_url = page.url or fallback_url
        except Exception:
            pass
        pre_checks = await self._evaluate_checks(page, selectors)

        await asyncio.sleep(0.12)

        post_url = pre_url
        try:
            post_url = page.url or pre_url
        except Exception:
            pass
        post_checks = await self._evaluate_checks(page, selectors)

        if pre_url != post_url:
            transition_hint = "url_changed"
        elif any((a.exists != b.exists or a.count != b.count) for a, b in zip(pre_checks, post_checks)):
            transition_hint = "dom_changed"
        else:
            transition_hint = "stable"

        return StepStateMarkers(
            pre_url=pre_url,
            post_url=post_url,
            pre_checks=pre_checks,
            post_checks=post_checks,
            transition_hint=transition_hint,
        )

    def _derive_marker_selectors(self, target: Target) -> list[tuple[str, str]]:
        """Derive key selectors for compact pre/post existence checks."""
        selectors: list[tuple[str, str]] = []

        if target.selectors and target.selectors.css:
            selectors.append(("target_element", target.selectors.css))

        for node in target.context_path or []:
            attrs = node.attributes or {}
            if attrs.get("id"):
                selectors.append(("target_container", f"#{attrs['id']}"))
                break
            data_attrs = [(k, v) for k, v in attrs.items() if k.startswith("data-") and v]
            if data_attrs:
                k, v = data_attrs[0]
                selectors.append(("target_container", f'[{k}="{v}"]'))
                break
            if node.tag:
                selectors.append(("target_container", node.tag))
                break

        row_identity = (target.disambiguators or {}).get("row_identity") or {}
        row_data_attrs = row_identity.get("data_attrs") or {}
        if row_data_attrs:
            k, v = next(iter(row_data_attrs.items()))
            selectors.append(("mutation_anchor", f'[{k}="{v}"]'))
        elif row_identity.get("id"):
            selectors.append(("mutation_anchor", f"#{row_identity['id']}"))
        elif target.selectors and target.selectors.css:
            selectors.append(("mutation_anchor", target.selectors.css))

        dedup: list[tuple[str, str]] = []
        seen = set()
        for name, selector in selectors:
            key = (name, selector)
            if selector and key not in seen:
                dedup.append((name, selector))
                seen.add(key)
        return dedup[:3]

    async def _evaluate_checks(
        self,
        page: Page,
        selectors: list[tuple[str, str]],
    ) -> list[DOMExistenceCheck]:
        checks: list[DOMExistenceCheck] = []
        for name, selector in selectors:
            count = 0
            try:
                count = await page.locator(selector).count()
            except Exception:
                count = 0
            checks.append(
                DOMExistenceCheck(
                    name=name,
                    selector=selector,
                    exists=count > 0,
                    count=count,
                )
            )
        return checks
