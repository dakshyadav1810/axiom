"""
Interaction Observer for Axiome Recording Engine.

Captures user interactions via Playwright event listeners and
CDP (Chrome DevTools Protocol) for comprehensive event capture.
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional
from playwright.async_api import BrowserContext, Page, CDPSession


@dataclass
class RawBrowserEvent:
    """
    Lossless raw browser event — every event the browser fires is captured
    here regardless of whether it passes curation filters.

    Attributes:
        event_seq: Monotonically increasing sequence number.
        event_type: Raw browser event type (click, type, blur, keypress, select, submit, navigate).
        timestamp: ISO-8601 timestamp string.
        url: Page URL at event time.
        raw_target: Minimal target metadata straight from the browser (tag, id, classes, text snippet).
        input_value: Value for type/select events.
        interactive_ancestor_found: Whether resolveToInteractive found an ancestor.
        curated: Whether this event was promoted into the curated step flow.
    """
    event_seq: int
    event_type: str
    timestamp: str
    url: str = ""
    raw_target: Optional[dict[str, Any]] = None
    input_value: Optional[str] = None
    interactive_ancestor_found: bool = True
    curated: bool = False
    context_id: Optional[str] = None
    opener_context_id: Optional[str] = None
    page_ref: Optional[str] = None


@dataclass
class InteractionEvent:
    """
    Raw interaction event data captured from the browser.
    
    Attributes:
        event_type: Type of interaction (click, type, submit, navigate, select)
        timestamp: When the interaction occurred
        element_data: DOM element data from JavaScript evaluation
        input_value: Input value for type/select events
        url: Page URL at interaction time
        navigation_url: New URL for navigation events
    """
    event_type: str
    timestamp: datetime
    element_data: Optional[dict[str, Any]] = None
    input_value: Optional[str] = None
    url: str = ""
    navigation_url: Optional[str] = None
    context_id: Optional[str] = None
    opener_context_id: Optional[str] = None
    page_ref: Optional[str] = None


class InteractionObserver:
    """
    Observes and captures user interactions across all pages in a context.
    
    Uses a combination of Playwright event listeners and injected
    JavaScript to capture comprehensive interaction data.
    
    The observer captures:
    - Click events with full element data
    - Keyboard input with final values
    - Form submissions
    - Page navigations
    - Select/option changes
    
    Example:
        observer = InteractionObserver()
        await observer.attach(page)
        observer.on_interaction(my_callback)
        # ... user interacts with page ...
        await observer.detach()
    """
    
    # Debounce window in milliseconds
    DEBOUNCE_MS = 100
    # Click dedup window — prevents event capture phase from creating duplicates
    CLICK_DEDUP_MS = 75
    
    def __init__(self):
        """Initialize the interaction observer."""
        self._page: Optional[Page] = None
        self._context: Optional[BrowserContext] = None
        self._cdp_session: Optional[CDPSession] = None
        self._callbacks: list[Callable[[InteractionEvent], None]] = []
        self._raw_callbacks: list[Callable[[RawBrowserEvent], None]] = []
        self._active_page_callbacks: list[Callable[[Optional[Page], dict[str, Optional[str]]], None]] = []
        self._attached = False
        self._last_event_time: float = 0
        self._pending_input: Optional[dict[str, Any]] = None
        self._input_timer: Optional[asyncio.Task] = None
        # Raw event stream — monotonically increasing sequence
        self._raw_event_seq: int = 0
        self._raw_events: list[RawBrowserEvent] = []
        # Click deduplication — track the last click's element identity to prevent
        # event capture phase from creating duplicates when a label wraps an input
        self._last_click_element_key: Optional[str] = None
        self._last_click_time: float = 0
        # Page/context registry so events include deterministic context metadata.
        self._ctx_seq: int = 0
        self._page_seq: int = 0
        self._page_ref_to_context_id: dict[str, str] = {}
        self._page_ids_to_context_id: dict[int, str] = {}
        self._context_id_to_page: dict[str, Page] = {}
        self._context_id_to_opener: dict[str, Optional[str]] = {}
        self._context_id_to_page_ref: dict[str, str] = {}
        self._registry_lock = asyncio.Lock()
        self._active_context_id: Optional[str] = None
    
    def get_page_by_context_id(self, context_id: Optional[str]) -> Optional[Page]:
        """Return the current Page for a recorded context id, if still open."""
        if not context_id:
            return None
        page = self._context_id_to_page.get(context_id)
        if page and not page.is_closed():
            return page
        return None

    def get_page_context_metadata(self, page: Optional[Page]) -> dict[str, Optional[str]]:
        """Return {context_id, opener_context_id, page_ref} for a page."""
        if not page:
            return {"context_id": None, "opener_context_id": None, "page_ref": None}
        context_id = self._page_ids_to_context_id.get(id(page))
        if not context_id:
            return {"context_id": None, "opener_context_id": None, "page_ref": None}
        return {
            "context_id": context_id,
            "opener_context_id": self._context_id_to_opener.get(context_id),
            "page_ref": self._context_id_to_page_ref.get(context_id),
        }

    def get_active_page(self) -> Optional[Page]:
        """Return the observer's current active page."""
        if self._page and not self._page.is_closed():
            return self._page
        if self._active_context_id:
            return self.get_page_by_context_id(self._active_context_id)
        return None

    def on_active_page_changed(
        self,
        callback: Callable[[Optional[Page], dict[str, Optional[str]]], None],
    ) -> None:
        """Register a callback invoked whenever the observer's active page changes."""
        self._active_page_callbacks.append(callback)

    def remove_active_page_callback(
        self,
        callback: Callable[[Optional[Page], dict[str, Optional[str]]], None],
    ) -> None:
        """Remove a previously registered active-page callback."""
        if callback in self._active_page_callbacks:
            self._active_page_callbacks.remove(callback)

    def _emit_active_page_changed(self, page: Optional[Page]) -> None:
        """Notify listeners that the observer active page/context changed."""
        metadata = self.get_page_context_metadata(page)
        for callback in list(self._active_page_callbacks):
            try:
                callback(page, metadata)
            except Exception:
                pass

    def _set_active_page(
        self,
        page: Optional[Page],
        context_id: Optional[str],
    ) -> bool:
        """Set the authoritative active page and notify listeners on change."""
        if page is not None and page.is_closed():
            page = None
        if page is None and context_id:
            page = self.get_page_by_context_id(context_id)
        if page is not None and context_id is None:
            context_id = self._page_ids_to_context_id.get(id(page))

        current_page = self.get_active_page()
        current_context_id = self._active_context_id
        if current_page is page and current_context_id == context_id:
            self._page = page
            self._active_context_id = context_id
            return False

        self._page = page
        self._active_context_id = context_id
        self._emit_active_page_changed(page)
        return True
    
    async def attach(self, page: Page) -> None:
        """
        Attach interaction listeners to a Playwright page.
        
        Injects JavaScript event handlers and sets up page event
        listeners for comprehensive interaction capture.
        
        Args:
            page: Playwright Page instance to observe
            
        Raises:
            RuntimeError: If already attached to a page
        """
        if self._attached:
            raise RuntimeError("Observer already attached to a page")
        
        self._page = page
        self._context = page.context
        self._attached = True

        # Expose callback function to JavaScript at context level so every
        # existing/future tab and popup can report interactions.
        await self._context.expose_binding(
            "__axiom_record_interaction",
            self._handle_js_interaction,
        )

        # Init script applies to every future document in every page.
        await self._context.add_init_script(self._capture_script_source())

        # Track all existing pages (the initial page can already have navigated
        # during auth/session bootstrap before observer attach).
        for existing in list(self._context.pages):
            await self._register_page(existing)

        # Register future pages (new tabs, popups, window.open).
        self._context.on("page", lambda p: asyncio.create_task(self._register_page(p)))
    
    async def detach(self) -> None:
        """
        Remove all interaction listeners from the page.
        
        Cleans up JavaScript handlers and Playwright event listeners.
        """
        if not self._attached:
            return
        
        # Flush any pending input before detaching so it isn't lost
        self._flush_pending_input()
        
        self._page = None
        self._context = None
        self._attached = False
    
    def on_interaction(self, callback: Callable[[InteractionEvent], None]) -> None:
        """
        Register a callback for interaction events.
        
        The callback will be invoked for each captured interaction
        with an InteractionEvent containing all relevant data.
        
        Args:
            callback: Function to call with InteractionEvent
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[InteractionEvent], None]) -> None:
        """
        Remove a previously registered callback.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def on_raw_event(self, callback: Callable[[RawBrowserEvent], None]) -> None:
        """Register a callback for raw (lossless) browser events."""
        self._raw_callbacks.append(callback)

    def get_raw_events(self) -> list[RawBrowserEvent]:
        """Return the full raw event log captured so far."""
        return list(self._raw_events)

    def _record_raw_event(
        self,
        *,
        event_type: str,
        url: str,
        raw_target: Optional[dict[str, Any]] = None,
        input_value: Optional[str] = None,
        interactive_ancestor_found: bool = True,
        curated: bool = False,
        context_id: Optional[str] = None,
        opener_context_id: Optional[str] = None,
        page_ref: Optional[str] = None,
    ) -> RawBrowserEvent:
        """Record a raw browser event and emit to raw callbacks."""
        self._raw_event_seq += 1
        raw = RawBrowserEvent(
            event_seq=self._raw_event_seq,
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            url=url,
            raw_target=raw_target,
            input_value=input_value,
            interactive_ancestor_found=interactive_ancestor_found,
            curated=curated,
            context_id=context_id,
            opener_context_id=opener_context_id,
            page_ref=page_ref,
        )
        self._raw_events.append(raw)
        for cb in self._raw_callbacks:
            try:
                cb(raw)
            except Exception:
                pass
        return raw

    async def _register_page(self, page: Page) -> None:
        """Register a page in the context registry and inject capture script."""
        context_id: Optional[str] = None
        opener_context_id: Optional[str] = None
        async with self._registry_lock:
            page_key = id(page)
            if page_key in self._page_ids_to_context_id:
                return

            self._ctx_seq += 1
            self._page_seq += 1
            context_id = f"ctx_{self._ctx_seq}"
            page_ref = f"page_{self._page_seq}"
            try:
                opener = await page.opener()
                opener_context_id = self._page_ids_to_context_id.get(id(opener)) if opener else None
            except Exception:
                opener_context_id = None

            self._page_ids_to_context_id[page_key] = context_id
            self._context_id_to_page[context_id] = page
            self._context_id_to_opener[context_id] = opener_context_id
            self._context_id_to_page_ref[context_id] = page_ref
            self._page_ref_to_context_id[page_ref] = context_id
            if self._active_context_id is None:
                self._active_context_id = context_id

        # Keep page_ref stable across same-page navigations.
        try:
            await page.add_init_script(
                f"window.__axiom_page_ref = {json.dumps(page_ref)};"
            )
        except Exception:
            pass
        try:
            await page.evaluate("(ref) => { window.__axiom_page_ref = ref; }", page_ref)
        except Exception:
            pass

        await self._inject_capture_script(page)
        page.on("load", lambda: asyncio.create_task(self._inject_capture_script(page)))
        page.on("close", lambda: self._handle_page_closed(page))
        # Immediate-follow policy: only child pages opened from the current
        # active context steal focus. Unrelated/background pages do not.
        if context_id and opener_context_id and opener_context_id == self._active_context_id:
            self._set_active_page(page, context_id)
        elif context_id and self._page is None:
            self._set_active_page(page, context_id)

    def _handle_page_closed(self, page: Page) -> None:
        """Clean up registry entries for closed pages."""
        context_id = self._page_ids_to_context_id.pop(id(page), None)
        if not context_id:
            return
        opener_context_id = self._context_id_to_opener.pop(context_id, None)
        self._context_id_to_page.pop(context_id, None)
        page_ref = self._context_id_to_page_ref.pop(context_id, None)
        if page_ref:
            self._page_ref_to_context_id.pop(page_ref, None)
        if self._active_context_id == context_id:
            fallback_page = self.get_page_by_context_id(opener_context_id)
            fallback_context_id = opener_context_id if fallback_page else None
            if fallback_page is None:
                for cid, candidate in self._context_id_to_page.items():
                    if candidate and not candidate.is_closed():
                        fallback_page = candidate
                        fallback_context_id = cid
                        break
            self._set_active_page(fallback_page, fallback_context_id)

    async def _inject_capture_script(self, page: Page) -> None:
        """Inject the JavaScript interaction capture code into one page."""
        max_retries = 3
        for attempt in range(max_retries):
            script = self._capture_script_source()
            try:
                await page.evaluate(script)
                return  # Success
            except Exception:
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.2 * (attempt + 1))
                # Final attempt failure — page may have navigated, ignore

    def _capture_script_source(self) -> str:
        """Shared JS source for init script + best-effort runtime injection."""
        return """
        (() => {
            // Prevent double injection
            if (window.__axiom_injected) return;
            window.__axiom_injected = true;
            
            // Helper to extract element data
            function getElementData(element) {
                if (!element || !element.tagName) return null;
                
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
                    // Implicit roles
                    const tagRoles = {
                        'button': 'button',
                        'a': 'link',
                        'input': element.type === 'checkbox' ? 'checkbox' : 
                                 element.type === 'radio' ? 'radio' :
                                 element.type === 'submit' ? 'button' : 'textbox',
                        'select': 'combobox',
                        'textarea': 'textbox',
                        'img': 'img',
                        'nav': 'navigation',
                        'main': 'main',
                        'header': 'banner',
                        'footer': 'contentinfo',
                        'form': 'form',
                        'table': 'table',
                        'ul': 'list',
                        'ol': 'list',
                        'li': 'listitem'
                    };
                    role = tagRoles[element.tagName.toLowerCase()] || null;
                }
                
                // Get text content (direct text, not nested)
                let text = '';
                for (const node of element.childNodes) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        text += node.textContent;
                    }
                }
                text = text.trim();
                if (!text && element.tagName === 'INPUT') {
                    text = element.placeholder || '';
                }
                
                // --- Sibling index among same tag/role ---
                let siblingIndex = 0;
                let siblingCount = 0;
                let sib = element.previousElementSibling;
                while (sib) {
                    if (sib.tagName === element.tagName) siblingIndex++;
                    sib = sib.previousElementSibling;
                }
                sib = element.parentElement ? element.parentElement.children : [];
                for (let i = 0; i < sib.length; i++) {
                    if (sib[i].tagName === element.tagName) siblingCount++;
                }
                
                // --- Label text (explicit/implicit) ---
                let labelText = null;
                if (element.id) {
                    const labelEl = document.querySelector('label[for="' + CSS.escape(element.id) + '"]');
                    if (labelEl) labelText = (labelEl.innerText || '').trim();
                }
                if (!labelText) {
                    const parentLabel = element.closest('label');
                    if (parentLabel) labelText = (parentLabel.innerText || '').trim();
                }
                if (!labelText) {
                    labelText = element.getAttribute('aria-label') || null;
                }
                
                // --- Semantic text (multi-signal list) ---
                const semanticTextItems = [];
                if (text && text.length < 100) semanticTextItems.push(text);
                if (element.title) semanticTextItems.push(element.title);
                if (element.placeholder) semanticTextItems.push(element.placeholder);
                const ariaLbl = element.getAttribute('aria-label');
                if (ariaLbl && !semanticTextItems.includes(ariaLbl)) semanticTextItems.push(ariaLbl);
                if (labelText && !semanticTextItems.includes(labelText)) semanticTextItems.push(labelText);
                // Ancestor text hints
                let anc = element.parentElement;
                let ancDepth = 0;
                while (anc && ancDepth < 2) {
                    if (['li', 'tr', 'h1', 'h2', 'h3', 'h4', 'div'].includes(anc.tagName.toLowerCase())) {
                        const ancText = (anc.innerText || '').split('\\n')[0].trim();
                        if (ancText && ancText.length > 0 && ancText.length < 50 && !semanticTextItems.includes(ancText)) {
                            semanticTextItems.push(ancText);
                        }
                    }
                    anc = anc.parentElement;
                    ancDepth++;
                }
                
                // --- Extra attributes for resolver ---
                const extraAttributes = {
                    type: element.type || null,
                    name: element.name || null,
                    placeholder: element.placeholder || null,
                    href: element.getAttribute('href') || null,
                    role: role
                };
                
                // --- Scroll and viewport tracking ---
                const scrollX = window.scrollX || window.pageXOffset || 0;
                const scrollY = window.scrollY || window.pageYOffset || 0;
                const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
                const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
                
                // Generate CSS selector
                function getCssSelector(el) {
                    if (el.id) return '#' + CSS.escape(el.id);
                    
                    let selector = el.tagName.toLowerCase();
                    
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/).filter(c => c);
                        if (classes.length > 0) {
                            selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
                        }
                    }
                    
                    // Add nth-child for uniqueness
                    const parent = el.parentElement;
                    if (parent) {
                        const siblings = Array.from(parent.children).filter(
                            c => c.tagName === el.tagName
                        );
                        if (siblings.length > 1) {
                            const index = siblings.indexOf(el) + 1;
                            selector += ':nth-of-type(' + index + ')';
                        }
                    }
                    
                    return selector;
                }
                
                // Build full CSS path
                function getFullCssPath(el) {
                    const parts = [];
                    let current = el;
                    while (current && current !== document.body) {
                        parts.unshift(getCssSelector(current));
                        current = current.parentElement;
                    }
                    return parts.join(' > ');
                }
                
                // Generate XPath
                function getXPath(el) {
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
                
                // Get ancestors for context path (enriched with class, data-*, aria-*)
                function getAncestors(el) {
                    const ancestors = [];
                    let current = el.parentElement;
                    let depth = 0;
                    const maxDepth = 5;
                    
                    const semanticTags = new Set([
                        'form', 'dialog', 'section', 'article', 'aside', 'nav',
                        'main', 'header', 'footer', 'figure', 'fieldset',
                        'details', 'menu', 'search'
                    ]);
                    
                    while (current && current !== document.body && depth < maxDepth) {
                        const tag = current.tagName.toLowerCase();
                        const attrs = {};
                        
                        for (const attr of current.attributes || []) {
                            // Include id, class, data-*, aria-*, role, name, title
                            if (attr.name === 'id' || attr.name === 'class' ||
                                attr.name.startsWith('data-') || attr.name.startsWith('aria-') ||
                                attr.name === 'role' || attr.name === 'name' || attr.name === 'title') {
                                attrs[attr.name] = attr.value;
                            }
                        }
                        
                        // Only include semantic containers or elements with identifiers
                        const hasId = current.id;
                        const hasAriaLabel = current.getAttribute('aria-label');
                        const hasTestId = current.getAttribute('data-testid') ||
                                          current.getAttribute('data-test-id') ||
                                          current.getAttribute('data-cy');
                        const isSemantic = semanticTags.has(tag);
                        const hasRole = current.getAttribute('role');
                        
                        if (hasId || hasAriaLabel || hasTestId || isSemantic || hasRole) {
                            ancestors.push({
                                tag: tag,
                                role: current.getAttribute('role') || null,
                                attributes: attrs
                            });
                            depth++;
                        }
                        
                        current = current.parentElement;
                    }
                    
                    return ancestors;
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
                    ancestors: getAncestors(element),
                    // Rich fields for resolver pipeline
                    sibling_index: siblingIndex,
                    sibling_count: siblingCount,
                    label_text: labelText,
                    extra_index: siblingIndex,
                    extra_label: labelText,
                    extra_semantic_text: semanticTextItems,
                    extra_attributes: extraAttributes,
                    // Nearby/container text for disambiguation of repeated elements
                    nearby_text: (() => {
                        const containerTags = new Set(['tr', 'li', 'article', 'fieldset']);
                        const containerRoles = new Set(['row', 'listitem', 'group']);
                        let anc = element.parentElement;
                        let d = 0;
                        while (anc && anc.tagName !== 'BODY' && d < 6) {
                            const t = anc.tagName.toLowerCase();
                            const r = anc.getAttribute('role');
                            const isCard = anc.classList && (
                                anc.classList.contains('card') ||
                                anc.classList.contains('item') ||
                                anc.classList.contains('row')
                            );
                            if (containerTags.has(t) || containerRoles.has(r) || isCard) {
                                let txt = (anc.innerText || '').replace(/[\\n\\r]+/g, ' ').trim();
                                if (txt.length > 200) txt = txt.substring(0, 200);
                                return txt;
                            }
                            anc = anc.parentElement;
                            d++;
                        }
                        return '';
                    })(),
                    // Repeating-group detection for "vary from group"
                    repeating_group: (() => {
                        const groupContainerTags = new Set(['ul', 'ol', 'tbody', 'div', 'section', 'nav', 'main']);
                        const groupRoles = new Set(['list', 'listbox', 'grid', 'table', 'tablist', 'menu', 'group']);
                        const cardClasses = ['card', 'item', 'product', 'result', 'tile', 'option', 'entry'];
                        let anc = element.parentElement;
                        let depth = 0;
                        while (anc && anc.tagName !== 'BODY' && depth < 8) {
                            const parent = anc.parentElement;
                            if (!parent) break;
                            const tag = parent.tagName.toLowerCase();
                            const role = parent.getAttribute('role');
                            const isGroupContainer = groupContainerTags.has(tag) || groupRoles.has(role || '');
                            if (isGroupContainer) {
                                const sibTag = anc.tagName.toLowerCase();
                                const siblings = Array.from(parent.children).filter(c => c.tagName.toLowerCase() === sibTag);
                                if (siblings.length >= 2) {
                                    const idx = siblings.indexOf(anc);
                                    // Build a CSS selector for all siblings
                                    let groupSel = '';
                                    const parentId = parent.getAttribute('id');
                                    if (parentId) {
                                        groupSel = '#' + CSS.escape(parentId) + ' > ' + sibTag;
                                    } else {
                                        // Use nth-child-based parent selector
                                        let path = '';
                                        let p = parent;
                                        for (let i = 0; i < 3 && p && p.tagName !== 'BODY'; i++) {
                                            const pp = p.parentElement;
                                            if (!pp) break;
                                            const pSiblings = Array.from(pp.children);
                                            const pIdx = pSiblings.indexOf(p) + 1;
                                            path = ' > ' + p.tagName.toLowerCase() + ':nth-child(' + pIdx + ')' + path;
                                            p = pp;
                                        }
                                        groupSel = path.replace(/^ > /, '') + ' > ' + sibTag;
                                    }
                                    return {
                                        detected: true,
                                        group_selector: groupSel,
                                        sibling_count: siblings.length,
                                        sibling_index: idx,
                                        container_tag: tag,
                                        container_role: role || null,
                                    };
                                }
                            }
                            // Also detect card-like class patterns
                            const hasCardClass = cardClasses.some(c =>
                                anc.classList && anc.classList.contains(c)
                            );
                            if (hasCardClass && parent) {
                                const sibTag = anc.tagName.toLowerCase();
                                const siblings = Array.from(parent.children).filter(c => {
                                    if (c.tagName.toLowerCase() !== sibTag) return false;
                                    return cardClasses.some(cc => c.classList && c.classList.contains(cc));
                                });
                                if (siblings.length >= 2) {
                                    const idx = siblings.indexOf(anc);
                                    return {
                                        detected: true,
                                        group_selector: null, // Complex CSS; let executor use role-based matching
                                        sibling_count: siblings.length,
                                        sibling_index: idx,
                                        container_tag: parent.tagName.toLowerCase(),
                                        container_role: parent.getAttribute('role') || null,
                                    };
                                }
                            }
                            anc = parent;
                            depth++;
                        }
                        return { detected: false };
                    })(),
                    // Scroll and viewport context
                    scroll_position: { x: scrollX, y: scrollY },
                    absolute_position: {
                        x: rect.x + scrollX,
                        y: rect.y + scrollY,
                        width: rect.width,
                        height: rect.height
                    },
                    viewport: { width: viewportWidth, height: viewportHeight }
                };
            }
            
            // Shadow DOM helper: if target is inside a shadow root,
            // walk up to find the light-DOM host element for getElementData
            function resolveFromShadow(target) {
                let el = target;
                while (el) {
                    const root = el.getRootNode();
                    if (root instanceof ShadowRoot) {
                        // The host is in the light DOM or another shadow root
                        el = root.host;
                    } else {
                        return el;
                    }
                }
                return target;
            }
            
            // Hover-gate detector: walk up ancestors looking for elements
            // inside hover-triggered overlays (menus, dropdowns, tooltips).
            // Returns the hover TRIGGER element (the parent you hover to
            // reveal the overlay), not the overlay itself.
            function findHoverGateAncestor(element) {
                // Class substrings that indicate an overlay/hover-gated container
                const overlayIndicators = [
                    'overlay', 'dropdown', 'tooltip', 'popover', 'submenu',
                    'menu-item', 'hover', 'flyout', 'megamenu', 'popup',
                    'dropdown-menu', 'dropdown-content'
                ];
                
                // Strategy 1: Class-name detection.
                // Walk up from clicked element looking for an overlay container.
                // When found, continue upward past any nested overlays and return
                // the first NON-overlay ancestor as the hover trigger.
                let current = element;
                let depth = 0;
                let overlayFound = null;
                
                while (current && current !== document.body && depth < 8) {
                    const cls = (current.className || '').toString().toLowerCase();
                    const isOverlay = overlayIndicators.some(h => cls.includes(h));
                    
                    if (isOverlay) {
                        overlayFound = current;
                    } else if (overlayFound) {
                        // We climbed past the overlay — this is the hover trigger
                        return current;
                    }
                    
                    // Check data attributes for hover toggles
                    if (!overlayFound) {
                        if (current.getAttribute('data-hover') !== null ||
                            current.getAttribute('data-toggle') === 'hover') {
                            return current;
                        }
                    }
                    
                    current = current.parentElement;
                    depth++;
                }
                
                // If we found an overlay but ran out of ancestors, return the overlay's parent
                if (overlayFound && overlayFound.parentElement) {
                    return overlayFound.parentElement;
                }
                
                // Strategy 2: CSS transition detection.
                // Check ancestors that currently match :hover and have children with
                // position:absolute + opacity/visibility transitions (overlay pattern).
                try {
                    current = element.parentElement;
                    depth = 0;
                    while (current && current !== document.body && depth < 5) {
                        if (current.matches(':hover')) {
                            const children = current.children;
                            for (let i = 0; i < children.length; i++) {
                                const child = children[i];
                                const style = window.getComputedStyle(child);
                                const pos = style.position;
                                const trans = style.transition || style.webkitTransition || '';
                                const hasOverlayTransition = 
                                    trans.includes('opacity') || 
                                    trans.includes('visibility') ||
                                    trans.includes('transform');
                                if ((pos === 'absolute' || pos === 'fixed') && hasOverlayTransition) {
                                    if (child.contains(element)) {
                                        return current;
                                    }
                                }
                            }
                        }
                        current = current.parentElement;
                        depth++;
                    }
                } catch(e) {}
                
                return null;
            }
            
            // Bubble up to nearest interactive ancestor.
            // When a user clicks an <i>, <svg>, <span>, or <img> inside
            // a <button> or <a>, we record the interactive parent —
            // that is what the executor will see as a candidate.
            const INTERACTIVE_TAGS = new Set([
                'button', 'a', 'input', 'select', 'textarea', 'summary'
            ]);
            const INTERACTIVE_ROLES = new Set([
                'button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'option', 'switch'
            ]);
            function isProbablyInteractive(el) {
                if (!el || !el.tagName) return false;
                const tag = el.tagName.toLowerCase();
                if (INTERACTIVE_TAGS.has(tag)) return true;
                const role = (el.getAttribute('role') || '').toLowerCase();
                if (INTERACTIVE_ROLES.has(role)) return true;
                if (el.getAttribute('tabindex') !== null) return true;
                if (el.hasAttribute('onclick')) return true;
                if (el.getAttribute('contenteditable') === 'true') return true;
                if (el.getAttribute('href')) return true;
                if (el.getAttribute('data-action') || el.getAttribute('data-toggle')) return true;
                try {
                    const style = window.getComputedStyle(el);
                    if (style && style.cursor === 'pointer') return true;
                } catch (e) {}
                return false;
            }
            function resolveToInteractive(el) {
                // If the element itself is interactive, keep it
                if (isProbablyInteractive(el)) {
                    // Special case: if this is a label wrapping a radio/checkbox input,
                    // prefer the input element to avoid duplicate captures from event bubbling
                    if (el.tagName === 'LABEL') {
                        const input = el.querySelector('input[type="radio"], input[type="checkbox"]');
                        if (input) {
                            return input;
                        }
                    }
                    return el;
                }
                
                // Walk up to find closest interactive ancestor
                let current = el.parentElement;
                let depth = 0;
                while (current && current !== document.body && depth < 8) {
                    if (isProbablyInteractive(current)) {
                        // Special case: if we found a label, check if it wraps a radio/checkbox input
                        if (current.tagName === 'LABEL') {
                            const input = current.querySelector('input[type="radio"], input[type="checkbox"]');
                            if (input) {
                                return input;
                            }
                        }
                        return current;
                    }
                    current = current.parentElement;
                    depth++;
                }
                // No interactive ancestor found — skip this click.
                return null;
            }
            
            // Click handler (shadow DOM aware + interactive bubbling)
            document.addEventListener('click', (e) => {
                const rawTarget = resolveFromShadow(e.target);
                const target = resolveToInteractive(rawTarget);
                if (!target) {
                    // No interactive ancestor — emit raw-only event for lossless log
                    const rawData = getElementData(rawTarget);
                    if (rawData) {
                        window.__axiom_record_interaction({
                            type: 'click',
                            element: rawData,
                            timestamp: new Date().toISOString(),
                            _raw_only: true,
                            _interactive_ancestor: false,
                            page_ref: window.__axiom_page_ref || null
                        });
                    }
                    return;
                }
                const data = getElementData(target);
                if (data) {
                    // Hover recording is temporarily disabled.
                    window.__axiom_record_interaction({
                        type: 'click',
                        element: data,
                        timestamp: new Date().toISOString(),
                        _raw_only: false,
                        _interactive_ancestor: true,
                        page_ref: window.__axiom_page_ref || null
                    });
                }
            }, true);
            
            // Input handler (for type events — includes contenteditable)
            // NOTE: radio/checkbox fire 'input' on check-state change but
            // they are already captured by the click handler — recording
            // them here would produce a duplicate "Type" step.
            document.addEventListener('input', (e) => {
                const target = e.target;
                const isToggle = target.tagName === 'INPUT' &&
                    (target.type === 'radio' || target.type === 'checkbox');
                const isEditable = !isToggle &&
                    (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable);
                if (isEditable) {
                    const data = getElementData(target);
                    if (data) {
                        const value = target.isContentEditable ? (target.innerText || '') : target.value;
                        window.__axiom_record_interaction({
                            type: 'type',
                            element: data,
                            value: value,
                            timestamp: new Date().toISOString(),
                            page_ref: window.__axiom_page_ref || null
                        });
                    }
                }
            }, true);
            
            // Change handler (for select)
            document.addEventListener('change', (e) => {
                const target = e.target;
                if (target.tagName === 'SELECT') {
                    const data = getElementData(target);
                    if (data) {
                        window.__axiom_record_interaction({
                            type: 'select',
                            element: data,
                            value: target.value,
                            timestamp: new Date().toISOString(),
                            page_ref: window.__axiom_page_ref || null
                        });
                    }
                }
            }, true);
            
            // NOTE: No submit handler — form submissions are intrinsic events
            // caused by clicking a submit button or pressing Enter in a form
            // field. Both of those are already captured by the click and
            // keydown handlers. Recording submit separately leads to duplicate
            // steps that fail on replay.

            // Keydown handler — captures Enter/Tab keypresses that trigger
            // navigation or form submit without a visible button click
            document.addEventListener('keydown', (e) => {
                // Only record Enter and Tab — these are the keys that cause
                // side effects (form submit, focus change, navigation)
                if (e.key !== 'Enter' && e.key !== 'Tab') return;
                
                const target = resolveFromShadow(e.target);
                const data = getElementData(target);
                if (data) {
                    window.__axiom_record_interaction({
                        type: 'keypress',
                        element: data,
                        value: e.key,
                        timestamp: new Date().toISOString(),
                        page_ref: window.__axiom_page_ref || null
                    });
                }
            }, true);

            // Blur handler (for input consolidation — includes contenteditable)
            document.addEventListener('blur', (e) => {
                const target = e.target;
                const isEditable = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;
                if (isEditable) {
                    const data = getElementData(target);
                    if (data) {
                        const value = target.isContentEditable ? (target.innerText || '') : target.value;
                        window.__axiom_record_interaction({
                            type: 'blur',
                            element: data,
                            value: value,
                            timestamp: new Date().toISOString(),
                            page_ref: window.__axiom_page_ref || null
                        });
                    }
                }
            }, true);
        })();
        """
    
    async def _handle_js_interaction(self, source, payload) -> None:
        """Handle interaction events from JavaScript binding callback."""
        data: dict[str, Any]
        if isinstance(payload, dict):
            data = payload
        elif isinstance(payload, str):
            try:
                data = json.loads(payload)
            except Exception:
                return
        else:
            return

        source_page = getattr(source, "page", None) if source is not None else None
        if source_page is not None and id(source_page) not in self._page_ids_to_context_id:
            await self._register_page(source_page)

        metadata = self.get_page_context_metadata(source_page)
        page_ref = data.get("page_ref")
        context_id = metadata.get("context_id") or self._page_ref_to_context_id.get(page_ref)
        opener_context_id = metadata.get("opener_context_id")
        resolved_page_ref = metadata.get("page_ref") or page_ref

        if source_page is not None and not source_page.is_closed():
            self._set_active_page(source_page, context_id)
        elif context_id:
            self._set_active_page(self.get_page_by_context_id(context_id), context_id)

        event_type = data.get("type", "")
        element_data = data.get("element")
        value = data.get("value")
        is_raw_only = bool(data.get("_raw_only", False))
        interactive_ancestor = bool(data.get("_interactive_ancestor", True))
        if source_page is not None:
            try:
                page_url = source_page.url
            except Exception:
                page_url = self._page.url if self._page else ""
        else:
            page_url = self._page.url if self._page else ""

        # Build minimal raw target metadata for the raw event log
        raw_target = None
        if element_data and isinstance(element_data, dict):
            raw_target = {
                "tag": element_data.get("tag", ""),
                "id": element_data.get("id", ""),
                "classes": element_data.get("classes", ""),
                "text": (element_data.get("text") or "")[:120],
            }

        # Always record a raw event — this is the lossless stream
        self._record_raw_event(
            event_type=event_type,
            url=page_url,
            raw_target=raw_target,
            input_value=value,
            interactive_ancestor_found=interactive_ancestor,
            curated=not is_raw_only and event_type not in ("blur", "submit", "navigate"),
            context_id=context_id,
            opener_context_id=opener_context_id,
            page_ref=resolved_page_ref,
        )

        # If the click had no interactive ancestor, stop here (raw-only)
        if is_raw_only:
            return

        # If we switched tab/popup while typing, flush the old field value first.
        if (
            self._pending_input
            and self._pending_input.get("context_id")
            and context_id
            and self._pending_input.get("context_id") != context_id
        ):
            self._flush_pending_input()
        
        # Debounce rapid events of the same type
        current_time = asyncio.get_event_loop().time()
        
        # Click-specific deduplication — prevent event capture/bubble duplicates
        if event_type == "click":
            # Generate a unique key for this element
            element_key = None
            if element_data and isinstance(element_data, dict):
                tag = element_data.get("tag", "")
                elem_id = element_data.get("id", "")
                classes = element_data.get("classes", "")
                element_key = f"{tag}#{elem_id}.{classes}"
            
            # Check if this is a duplicate of the last click
            if (element_key and element_key == self._last_click_element_key and
                (current_time - self._last_click_time) * 1000 < self.CLICK_DEDUP_MS):
                # Skip this click — it's a duplicate from event capture/bubble phases
                return
            
            # Update click tracking
            self._last_click_element_key = element_key
            self._last_click_time = current_time
        
        if (current_time - self._last_event_time) * 1000 < self.DEBOUNCE_MS:
            if event_type == "type":
                # For typing, update pending input instead of creating new event
                self._pending_input = {
                    "element_data": element_data,
                    "value": value,
                    "url": page_url,
                    "context_id": context_id,
                    "opener_context_id": opener_context_id,
                    "page_ref": resolved_page_ref,
                }
                # Start/restart a flush timer so this input isn't silently lost
                if self._input_timer:
                    self._input_timer.cancel()

                async def emit_debounced_input():
                    await asyncio.sleep(1.5)
                    self._flush_pending_input()

                self._input_timer = asyncio.create_task(emit_debounced_input())
                return
        
        self._last_event_time = current_time
        
        # Handle typing with debounce - wait for pause in typing
        if event_type == "type":
            self._pending_input = {
                "element_data": element_data,
                "value": value,
                "url": page_url,
                "context_id": context_id,
                "opener_context_id": opener_context_id,
                "page_ref": resolved_page_ref,
            }
            
            # Cancel existing timer
            if self._input_timer:
                self._input_timer.cancel()
            
            # Set new timer to emit event after typing pause
            # Increased timeout to prevent fragmentation while typing
            async def emit_input():
                await asyncio.sleep(1.5)  # 1.5s pause
                self._flush_pending_input()
            
            self._input_timer = asyncio.create_task(emit_input())
            return
        
        # For any non-type event (click, submit, blur, select), flush pending input first
        self._flush_pending_input()
        
        # Don't record blur events themselves, just use them to flush
        if event_type == "blur":
            return
        
        # Create and emit event for non-type interactions
        event = InteractionEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            element_data=element_data,
            input_value=value,
            url=page_url,
            context_id=context_id,
            opener_context_id=opener_context_id,
            page_ref=resolved_page_ref,
        )
        
        self._emit_event(event)
    
    def _flush_pending_input(self) -> None:
        """Flush any pending input event immediately."""
        if self._input_timer:
            self._input_timer.cancel()
            self._input_timer = None
            
        if self._pending_input:
            event = InteractionEvent(
                event_type="type",
                timestamp=datetime.utcnow(),
                element_data=self._pending_input["element_data"],
                input_value=self._pending_input["value"],
                url=self._pending_input["url"],
                context_id=self._pending_input.get("context_id"),
                opener_context_id=self._pending_input.get("opener_context_id"),
                page_ref=self._pending_input.get("page_ref"),
            )
            self._pending_input = None
            self._emit_event(event)

    def _emit_event(self, event: InteractionEvent) -> None:
        """Emit an interaction event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                # Log but don't crash
                print(f"Warning: Callback error: {e}")
