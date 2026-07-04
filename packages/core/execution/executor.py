from __future__ import annotations

"""
Execution Engine - Playwright-based action executor.

This module handles:
- Browser lifecycle (launch, close)
- DOM element extraction
- Action execution (click, type, navigate, wait)
- Evidence collection (screenshots)
- Structured logging

Key principles:
- Explicit waits only
- No retries beyond one
- Deterministic execution
- Fail loudly on errors
"""

import asyncio
import os
import time
import re
import string
from typing import Optional, List, Any
from dataclasses import dataclass
from urllib.parse import urlsplit

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Locator,
    ElementHandle,
)

from ..models.resolver_models import (
    DOMElement,
    BoundingBox,
    ActionNode,
    ActionType,
    FlowDefinition,
    GeneralizationLevel,
    Preconditions,
    ResolutionResult,
    ActionResult,
    FlowResult,
    FailureReason,
    OnFailure,
)
from ..resolvers.resolver_router import ResolverRouter


# Default timeout for element operations (ms)
DEFAULT_TIMEOUT = 30000

# Wait before/after actions (ms)
ACTION_DELAY = 100
MAX_DIRECT_RECOVERY_ATTEMPTS = 2
MAX_RESOLVER_ATTEMPTS = 3
TRANSIENT_ACTION_ERROR_TOKENS = (
    "not attached",
    "detached",
    "intercepts pointer events",
    "element is not visible",
    "element is outside of the viewport",
    "element is not stable",
    "timeout",
)


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    result = text.lower()
    result = result.translate(str.maketrans("", "", string.punctuation))
    result = re.sub(r"\s+", " ", result).strip()
    return result


@dataclass
class ExecutorConfig:
    """Configuration for the executor."""
    headless: bool = False  # Browser visible by default for debugging
    timeout: int = DEFAULT_TIMEOUT
    screenshot_on_failure: bool = True
    verbose: bool = False
    environment_profile: str = "normal"  # normal | mobile | 3g
    replay_mode: str = "deterministic_first"  # deterministic_first | resolver_first | legacy
    resolver_fallback_policy: str = "balanced"  # balanced | strict | permissive
    screenshots_dir: Optional[str] = None  # Directory for failure screenshots; defaults to CWD
    # Auth session to inject before the test starts.
    # Format matches Playwright's storage_state() output:
    #   {
    #     "cookies": [{"name": ..., "value": ..., "domain": ..., "path": ..., ...}],
    #     "origins": [{"origin": "https://app.example.com",
    #                  "localStorage": {"token": "Bearer xyz"},
    #                  "sessionStorage": {}}]
    #   }
    # Cookies are injected at context level (no navigation needed).
    # localStorage/sessionStorage are injected per-origin via inject_storage_state().
    session_state: Optional[dict] = None


# ── ANSI color helpers ──────────────────────────────────────────────────
class _C:
    """ANSI color codes for terminal output."""
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BLUE   = "\033[94m"
    MAG    = "\033[95m"
    RESET  = "\033[0m"
    GRAY   = "\033[90m"

SEP_HEAVY = f"{_C.DIM}{'━' * 72}{_C.RESET}"
SEP_LIGHT = f"{_C.DIM}{'─' * 60}{_C.RESET}"
SEP_DOT   = f"{_C.GRAY}{'┄' * 50}{_C.RESET}"


def _el_desc(el, max_text: int = 40) -> str:
    """Build a compact human-readable description of a DOMElement."""
    parts = [f"{_C.CYAN}{el.tag}{_C.RESET}"]
    if el.role:
        parts.append(f'role="{el.role}"')
    if el.text:
        t = el.text[:max_text] + "…" if len(el.text) > max_text else el.text
        parts.append(f'{_C.GREEN}"{t}"{_C.RESET}')
    elif el.aria_label:
        parts.append(f'aria="{el.aria_label}"')
    if hasattr(el, 'node_id') and el.node_id:
        parts.append(f'{_C.GRAY}#{el.node_id}{_C.RESET}')
    return " ".join(parts)


class ActionLogger:
    """Rich structured logging for action execution with chain-of-thought display."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._step_num = 0

    # ── Step start ────────────────────────────────────────────────
    def log_action_start(self, action: ActionNode) -> None:
        """Log the start of an action with clear visual separator."""
        self._step_num += 1
        print(f"\n{SEP_HEAVY}")
        action_label = action.type.value.upper()
        value_hint = ""
        if action.value:
            v = action.value[:40] + "…" if len(action.value) > 40 else action.value
            value_hint = f'  →  "{v}"'

        target_hint = ""
        if action.target:
            t = action.target
            name_parts = []
            if hasattr(t, 'label') and t.label:
                name_parts.append(t.label)
            elif hasattr(t, 'semantic_text') and t.semantic_text:
                name_parts.append(t.semantic_text[0][:40])
            elif hasattr(t, 'tag') and t.tag:
                name_parts.append(t.tag)
            if name_parts:
                target_hint = f'  on  {_C.MAG}{name_parts[0]}{_C.RESET}'

        print(
            f"{_C.BOLD}STEP {self._step_num}  │  "
            f"{_C.YELLOW}{action_label}{_C.RESET}"
            f"{target_hint}{value_hint}"
        )
        print(SEP_LIGHT)

    # ── Resolution result ─────────────────────────────────────────
    def log_resolution(self, result: ResolutionResult) -> None:
        """Log the full resolver chain-of-thought."""

        # 1️. Resolver path
        path_str = " → ".join(
            f"{_C.CYAN}{r}{_C.RESET}" for r in (result.resolver_path or [])
        )
        print(f"  {_C.DIM}Resolver chain:{_C.RESET}  {path_str}")

        # 2. Funnel counts
        print(
            f"  {_C.DIM}Funnel:{_C.RESET}  "
            f"semantic={result.semantic_candidates_count}  "
            f"context={result.context_filtered_count}  "
            f"affordance={result.affordance_passed_count}"
        )

        if result.success:
            candidate = result.selected_candidate
            element = result.selected_element

            # 3. Per-resolver scores for the winner
            print(f"  {SEP_DOT}")
            print(f"  {_C.DIM}Score breakdown (selected):{_C.RESET}")
            print(
                f"    semantic  = {_C.BOLD}{candidate.semantic_score:.3f}{_C.RESET}   "
                f"context = {_C.BOLD}{candidate.context_score:.3f}{_C.RESET}   "
                f"selector = {_C.BOLD}{candidate.selector_score:.3f}{_C.RESET}   "
                f"affordance = {'✓' if candidate.affordance_passed else '✗'}"
            )
            print(
                f"    {_C.BOLD}final   = {candidate.score:.3f}{_C.RESET}"
            )
            print(
                f"    confidence = {_C.BOLD}{result.confidence_band}{_C.RESET}"
            )
            if result.confidence_warning:
                print(f"    {_C.DIM}{result.confidence_warning}{_C.RESET}")

            # 4. Reasons
            if candidate.reasons:
                print(f"  {_C.DIM}Reasons:{_C.RESET} {', '.join(candidate.reasons)}")

            # 5. Selected element
            print(f"  {SEP_DOT}")
            print(f"  {_C.GREEN}✔ Selected:{_C.RESET}  {_el_desc(element)}")

            # 6. Runner-up comparison (if any)
            if len(result.all_candidates) > 1:
                runner = result.all_candidates[1]
                margin = candidate.score - runner.score
                print(
                    f"  {_C.DIM}Runner-up:{_C.RESET}  {_el_desc(runner.element, 30)}  "
                    f"score={runner.score:.3f}  "
                    f"{_C.DIM}(margin {margin:+.3f}){_C.RESET}"
                )

            # 7. Top-N candidates table (verbose)
            if self.verbose and len(result.all_candidates) > 2:
                print(f"  {SEP_DOT}")
                print(f"  {_C.DIM}Top candidates:{_C.RESET}")
                for i, c in enumerate(result.all_candidates[:5]):
                    marker = "►" if i == 0 else " "
                    print(
                        f"    {marker} {c.score:.3f}  "
                        f"sem={c.semantic_score:.2f} ctx={c.context_score:.2f} "
                        f"sel={c.selector_score:.2f} aff={'✓' if c.affordance_passed else '✗'}  "
                        f"{_el_desc(c.element, 25)}"
                    )
        else:
            print(f"  {_C.RED}✘ FAILED:{_C.RESET}  {result.failure_reason.value}")
            print(f"    {result.failure_message}")
            if getattr(result, "confidence_band", None):
                print(f"    {_C.DIM}confidence={result.confidence_band}{_C.RESET}")

            # Show what we did have (top candidates if any)
            if result.all_candidates:
                print(f"  {_C.DIM}Closest candidates:{_C.RESET}")
                for c in result.all_candidates[:3]:
                    print(
                        f"    {c.score:.3f}  "
                        f"sem={c.semantic_score:.2f} ctx={c.context_score:.2f} "
                        f"sel={c.selector_score:.2f}  "
                        f"{_el_desc(c.element, 30)}"
                    )

    # ── Action result ─────────────────────────────────────────────
    def log_action_result(self, result: ActionResult) -> None:
        """Log action execution result."""
        if result.success:
            print(f"  {_C.GREEN}✔ EXECUTED{_C.RESET}  {_C.DIM}({result.time_taken_ms:.0f}ms){_C.RESET}")
        else:
            print(
                f"  {_C.RED}✘ EXEC FAILED:{_C.RESET}  "
                f"{result.failure_reason.value if result.failure_reason else 'unknown'}"
            )
            if result.failure_message:
                print(f"    {result.failure_message}")
            if result.screenshot_path:
                print(f"    {_C.DIM}Screenshot: {result.screenshot_path}{_C.RESET}")

    # ── Flow result ───────────────────────────────────────────────
    def log_flow_result(self, result: FlowResult) -> None:
        """Log overall flow result with summary."""
        print(f"\n{SEP_HEAVY}")
        status_color = _C.GREEN if result.success else _C.RED
        status_text = "PASS" if result.success else "FAIL"
        print(
            f"{_C.BOLD}FLOW RESULT:  "
            f"{status_color}{status_text}{_C.RESET}  "
            f"({result.actions_passed}/{result.actions_executed} passed, "
            f"{result.total_time_ms:.0f}ms)"
        )

        # Per-step mini summary
        if result.action_results:
            print(SEP_LIGHT)
            for i, ar in enumerate(result.action_results, 1):
                icon = f"{_C.GREEN}✔{_C.RESET}" if ar.success else f"{_C.RED}✘{_C.RESET}"
                fail_hint = ""
                if not ar.success and ar.failure_reason:
                    fail_hint = f"  {_C.RED}{ar.failure_reason.value}{_C.RESET}"
                print(f"  Step {i:>2}  {icon}  action={ar.action_id}{fail_hint}")

        print(SEP_HEAVY)


class Executor:
    """
    Playwright-based action executor.
    
    Handles browser automation and action execution.
    Uses the resolver router for element selection.
    """
    
    def __init__(self, config: Optional[ExecutorConfig] = None):
        """Initialize executor with configuration."""
        self.config = config or ExecutorConfig()
        self.logger = ActionLogger(verbose=self.config.verbose)
        self.router = ResolverRouter()
        
        # Browser state
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._cdp_session = None

        # Instance-scoped round-robin counters (not class-level — each Executor
        # instance gets a fresh counter so consecutive test runs don't bleed state)
        self._group_round_robin_counters: dict = {}
        # Runtime context registry (tabs/popups).
        self._runtime_ctx_seq: int = 0
        self._runtime_page_to_id: dict[int, str] = {}
        self._runtime_id_to_page: dict[str, Page] = {}
        self._runtime_id_to_opener: dict[str, Optional[str]] = {}
        self._recorded_to_runtime: dict[str, str] = {}
        self._active_context_id: Optional[str] = None
    
    async def launch(self) -> None:
        """Launch browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
        )
        context_kwargs = {}
        if self.config.environment_profile == "mobile":
            context_kwargs["viewport"] = {"width": 375, "height": 812}
        self._context = await self._browser.new_context(**context_kwargs)
        self._page = await self._context.new_page()
        self._context.on("page", lambda p: asyncio.create_task(self._register_runtime_page(p)))
        initial_runtime_id = await self._register_runtime_page(self._page)
        self._active_context_id = initial_runtime_id

        # ── Cookie injection (context-level, no navigation needed) ──
        if self.config.session_state:
            cookies = self.config.session_state.get("cookies") or []
            if cookies:
                try:
                    # Playwright requires sameSite values to be title-cased
                    # ("Strict"/"Lax"/"None").  Exported cookies from DevTools
                    # or Playwright itself sometimes arrive lowercase — normalise.
                    _SAME_SITE_MAP = {"strict": "Strict", "lax": "Lax", "none": "None"}
                    normalised = []
                    for c in cookies:
                        c = dict(c)
                        ss = c.get("sameSite")
                        if isinstance(ss, str):
                            c["sameSite"] = _SAME_SITE_MAP.get(ss.lower(), ss)
                        normalised.append(c)
                    await self._context.add_cookies(normalised)
                    print(f"  [auth] Injected {len(normalised)} cookie(s) into browser context")
                except Exception as cookie_err:
                    print(f"  [auth] Cookie injection warning: {cookie_err}")

        if self.config.environment_profile == "3g":
            self._cdp_session = await self._context.new_cdp_session(self._page)
            await self._cdp_session.send("Network.enable")
            await self._cdp_session.send(
                "Network.emulateNetworkConditions",
                {
                    "offline": False,
                    "latency": 300,
                    "downloadThroughput": 75000,
                    "uploadThroughput": 25000,
                },
            )
        
        # Set default timeout
        self._page.set_default_timeout(self.config.timeout)
    
    async def inject_storage_state(self, base_url: str = "") -> None:
        """Inject localStorage / sessionStorage from config.session_state.

        Must be called AFTER launch() and BEFORE the test's first page.goto().
        Cookies are already handled in launch(); this only handles storage.

        For each origin listed in session_state["origins"] the method:
          1. Navigates to that origin (required by same-origin policy).
          2. Evaluates JS to set every localStorage / sessionStorage key.
          3. Navigates back to about:blank so the caller's own goto() starts fresh.
        """
        if not self.config.session_state:
            return
        origins = self.config.session_state.get("origins") or []
        if not origins:
            return

        injected_origins: list[str] = []
        for entry in origins:
            origin = (entry.get("origin") or "").rstrip("/")
            ls_data = entry.get("localStorage") or {}
            ss_data = entry.get("sessionStorage") or {}
            if not origin or (not ls_data and not ss_data):
                continue
            try:
                # Navigate to the target origin so we have same-origin access
                await self._page.goto(origin, wait_until="domcontentloaded", timeout=10000)
                # Verify we actually landed on the intended origin (guard against redirects)
                actual_origin = self._page.url.split("?")[0].rstrip("/")
                if not actual_origin.startswith(origin.split("?")[0].rstrip("/")):
                    print(f"  [auth] Skipping storage for {origin}: redirected to {actual_origin[:60]}")
                    continue
                if ls_data:
                    await self._page.evaluate(
                        """(data) => {
                            for (const [k, v] of Object.entries(data))
                                localStorage.setItem(k, typeof v === 'string' ? v : JSON.stringify(v));
                        }""",
                        ls_data,
                    )
                if ss_data:
                    await self._page.evaluate(
                        """(data) => {
                            for (const [k, v] of Object.entries(data))
                                sessionStorage.setItem(k, typeof v === 'string' ? v : JSON.stringify(v));
                        }""",
                        ss_data,
                    )
                injected_origins.append(origin)
            except Exception as err:
                print(f"  [auth] Storage injection warning for {origin}: {err}")

        if injected_origins:
            print(f"  [auth] Injected storage for origin(s): {', '.join(injected_origins)}")
            # Return to a neutral page so caller's goto() is the first real navigation
            try:
                await self._page.goto("about:blank")
            except Exception:
                pass

    async def close(self) -> None:
        """Close browser and clean up."""
        if self._cdp_session:
            try:
                await self._cdp_session.detach()
            except Exception:
                pass
            self._cdp_session = None
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _register_runtime_page(self, page: Page) -> str:
        """Assign a runtime context id to a Playwright page."""
        page_key = id(page)
        existing = self._runtime_page_to_id.get(page_key)
        if existing:
            return existing

        self._runtime_ctx_seq += 1
        runtime_id = f"ctx_{self._runtime_ctx_seq}"
        opener_runtime_id: Optional[str] = None
        try:
            opener = await page.opener()
            opener_runtime_id = self._runtime_page_to_id.get(id(opener)) if opener else None
        except Exception:
            opener_runtime_id = None

        self._runtime_page_to_id[page_key] = runtime_id
        self._runtime_id_to_page[runtime_id] = page
        self._runtime_id_to_opener[runtime_id] = opener_runtime_id
        page.set_default_timeout(self.config.timeout)
        page.on("close", lambda: self._handle_runtime_page_closed(runtime_id, page))
        return runtime_id

    def _handle_runtime_page_closed(self, runtime_id: str, page: Page) -> None:
        """Remove closed pages from runtime context registry."""
        self._runtime_page_to_id.pop(id(page), None)
        self._runtime_id_to_page.pop(runtime_id, None)
        opener_runtime_id = self._runtime_id_to_opener.pop(runtime_id, None)
        if self._active_context_id == runtime_id:
            self._active_context_id = None
            self._page = None
            opener_page = self._runtime_id_to_page.get(opener_runtime_id) if opener_runtime_id else None
            if opener_page and not opener_page.is_closed():
                self._active_context_id = opener_runtime_id
                self._page = opener_page
                return
            for candidate_id, candidate_page in self._runtime_id_to_page.items():
                if candidate_page and not candidate_page.is_closed():
                    self._active_context_id = candidate_id
                    self._page = candidate_page
                    break

    async def _ensure_runtime_registry(self) -> None:
        """Ensure all currently open pages are present in registry."""
        if not self._context:
            return
        for page in list(self._context.pages):
            if id(page) not in self._runtime_page_to_id:
                await self._register_runtime_page(page)

    @staticmethod
    def _normalize_url(url: Optional[str]) -> str:
        raw = str(url or "").strip()
        if not raw:
            return ""
        try:
            parsed = urlsplit(raw)
            if not parsed.scheme:
                return raw
            path = parsed.path or "/"
            query = f"?{parsed.query}" if parsed.query else ""
            return f"{parsed.scheme}://{parsed.netloc}{path}{query}"
        except Exception:
            return raw

    async def _activate_runtime_page(self, runtime_id: str) -> bool:
        page = self._runtime_id_to_page.get(runtime_id)
        if not page or page.is_closed():
            return False
        self._page = page
        self._active_context_id = runtime_id
        try:
            await page.bring_to_front()
        except Exception:
            pass
        return True

    async def _align_action_context(self, action: ActionNode) -> Optional[str]:
        """Align the active Playwright page with action's recorded context."""
        recorded_context_id = (action.context_id or "").strip() or None
        if not recorded_context_id and action.type == ActionType.SWITCH_CONTEXT:
            recorded_context_id = (action.value or "").strip() or None
        if not recorded_context_id:
            return None

        await self._ensure_runtime_registry()
        available_runtime_ids = [
            rid for rid, page in self._runtime_id_to_page.items()
            if page and not page.is_closed()
        ]
        mapped_runtime_ids = set(self._recorded_to_runtime.values())
        unmapped_runtime_ids = [
            rid for rid in available_runtime_ids if rid not in mapped_runtime_ids
        ]

        # 1) Exact mapped context id
        mapped_runtime_id = self._recorded_to_runtime.get(recorded_context_id)
        if mapped_runtime_id and await self._activate_runtime_page(mapped_runtime_id):
            return None

        recorded_url = self._normalize_url(
            action.recorded_url
            or (action.target.url if action.target and action.target.url else "")
        )
        expected_opener_runtime_id = None
        if action.opener_context_id:
            expected_opener_runtime_id = self._recorded_to_runtime.get(action.opener_context_id)

        def _score_candidates(runtime_ids: list[str]) -> list[str]:
            def _ctx_num(value: str) -> int:
                try:
                    return int(value.split("_", 1)[1])
                except Exception:
                    return 10**9
            return sorted(runtime_ids, key=_ctx_num)

        # 2) Unmapped page matching opener + URL.
        # Only execute this branch when at least one signal is present.
        if expected_opener_runtime_id or recorded_url:
            opener_url_candidates: list[str] = []
            for runtime_id in unmapped_runtime_ids:
                if expected_opener_runtime_id and self._runtime_id_to_opener.get(runtime_id) != expected_opener_runtime_id:
                    continue
                page = self._runtime_id_to_page.get(runtime_id)
                if not page or page.is_closed():
                    continue
                if recorded_url and self._normalize_url(page.url) != recorded_url:
                    continue
                opener_url_candidates.append(runtime_id)
            if opener_url_candidates:
                chosen = _score_candidates(opener_url_candidates)[0]
                self._recorded_to_runtime[recorded_context_id] = chosen
                opener_runtime_id = self._runtime_id_to_opener.get(chosen)
                if action.opener_context_id and action.opener_context_id not in self._recorded_to_runtime and opener_runtime_id:
                    self._recorded_to_runtime[action.opener_context_id] = opener_runtime_id
                await self._activate_runtime_page(chosen)
                return None

        # 3) URL-only candidate
        if recorded_url:
            url_candidates = []
            for runtime_id in unmapped_runtime_ids:
                page = self._runtime_id_to_page.get(runtime_id)
                if page and not page.is_closed() and self._normalize_url(page.url) == recorded_url:
                    url_candidates.append(runtime_id)
            if not url_candidates:
                for runtime_id in available_runtime_ids:
                    page = self._runtime_id_to_page.get(runtime_id)
                    if page and not page.is_closed() and self._normalize_url(page.url) == recorded_url:
                        url_candidates.append(runtime_id)
            if url_candidates:
                chosen = _score_candidates(url_candidates)[0]
                self._recorded_to_runtime[recorded_context_id] = chosen
                opener_runtime_id = self._runtime_id_to_opener.get(chosen)
                if action.opener_context_id and action.opener_context_id not in self._recorded_to_runtime and opener_runtime_id:
                    self._recorded_to_runtime[action.opener_context_id] = opener_runtime_id
                await self._activate_runtime_page(chosen)
                return None

        # 4) Single unmapped-page fallback
        if len(unmapped_runtime_ids) == 1:
            chosen = unmapped_runtime_ids[0]
            self._recorded_to_runtime[recorded_context_id] = chosen
            opener_runtime_id = self._runtime_id_to_opener.get(chosen)
            if action.opener_context_id and action.opener_context_id not in self._recorded_to_runtime and opener_runtime_id:
                self._recorded_to_runtime[action.opener_context_id] = opener_runtime_id
            await self._activate_runtime_page(chosen)
            return None

        # 5) Context conflict
        available = ", ".join(sorted(available_runtime_ids)) if available_runtime_ids else "none"
        return (
            f"Could not align action context '{recorded_context_id}'"
            f" (opener={action.opener_context_id or 'none'}, url={recorded_url or 'none'})."
            f" Available runtime contexts: {available}"
        )
    
    async def run_flow(self, flow: FlowDefinition) -> FlowResult:
        """
        Execute a complete flow.
        
        Args:
            flow: The flow definition to execute
        
        Returns:
            FlowResult with all action results
        """
        start_time = time.time()
        
        result = FlowResult(
            success=True,
            actions_executed=0,
            actions_passed=0,
            actions_failed=0,
        )
        
        try:
            # Launch browser
            await self.launch()
            
            # Navigate to start URL
            print(SEP_HEAVY)
            print(f"{_C.BOLD}FLOW:{_C.RESET}  {flow.name if hasattr(flow, 'name') else 'unnamed'}")
            print(f"{_C.DIM}URL:{_C.RESET}   {flow.start_url}")
            print(f"{_C.DIM}Steps:{_C.RESET} {len(flow.actions)}")
            print(SEP_HEAVY)
            print(f"Navigating to: {flow.start_url}")
            await self._page.goto(flow.start_url, wait_until="domcontentloaded")
            
            # Execute each action
            for action in flow.actions:
                self.logger.log_action_start(action)
                
                action_result = await self._execute_action(action)
                
                # Handle retry_once: if failed, wait and retry one time
                if not action_result.success and action.on_failure == OnFailure.RETRY_ONCE:
                    print(f"  Retrying action {action.id} (retry_once)...")
                    await asyncio.sleep(1.0)
                    self.router._dom_lookup = {}  # Force DOM re-extraction
                    action_result = await self._execute_action(action)
                
                result.action_results.append(action_result)
                result.actions_executed += 1
                
                if action_result.success:
                    result.actions_passed += 1
                else:
                    result.actions_failed += 1
                    
                    # Check failure policy (retry_once already retried above, treat as abort)
                    if action.on_failure in (OnFailure.ABORT, OnFailure.RETRY_ONCE):
                        result.success = False
                        result.failure_reason = action_result.failure_reason
                        break
            
            # Overall success if all actions passed
            result.success = result.actions_failed == 0
            
        except Exception as e:
            result.success = False
            result.failure_reason = FailureReason.NAVIGATION_FAILED
            print(f"Flow execution error: {e}")
        
        finally:
            await self.close()
        
        result.total_time_ms = (time.time() - start_time) * 1000
        self.logger.log_flow_result(result)
        
        return result
    
    async def _execute_action(self, action: ActionNode) -> ActionResult:
        """
        Execute a single action.
        
        Resolves the target element and performs the action.
        """
        start_time = time.time()
        
        result = ActionResult(
            action_id=action.id,
            success=False,
            selection_source="none",
        )
        attempt_trace: list[dict[str, Any]] = []
        result.attempt_trace = attempt_trace

        try:
            context_error = await self._align_action_context(action)
            if context_error:
                result.failure_reason = FailureReason.CONTEXT_CONFLICT
                result.failure_message = context_error
                result.time_taken_ms = (time.time() - start_time) * 1000
                self.logger.log_action_result(result)
                return result

            # Handle non-element actions first.
            if action.type in (
                ActionType.NAVIGATE,
                ActionType.WAIT,
                ActionType.GO_BACK,
                ActionType.REFRESH,
                ActionType.WAIT_FOR_STABLE,
                ActionType.HOVER,
                ActionType.SWITCH_CONTEXT,
            ):
                result.selection_source = "none"
                # ── Precondition check for non-element actions (no element locator available)
                if action.preconditions:
                    prec_ok, prec_msg = await self._check_preconditions(action.preconditions, None)
                    if not prec_ok:
                        result.failure_reason = FailureReason.STATE_BLOCKED
                        result.failure_message = f"Precondition failed: {prec_msg}"
                        result.time_taken_ms = (time.time() - start_time) * 1000
                        self.logger.log_action_result(result)
                        return result
                if action.type == ActionType.NAVIGATE:
                    result = await self._execute_navigate(action, result)
                elif action.type == ActionType.WAIT:
                    result = await self._execute_wait(action, result)
                elif action.type == ActionType.GO_BACK:
                    result = await self._execute_go_back(result)
                elif action.type == ActionType.REFRESH:
                    result = await self._execute_refresh(result)
                elif action.type == ActionType.WAIT_FOR_STABLE:
                    result = await self._execute_wait_for_stable(result)
                elif action.type == ActionType.HOVER:
                    result.success = True
                    self._record_attempt(
                        attempt_trace,
                        phase="action",
                        strategy="hover_disabled",
                        status="skipped",
                    )
                    print("  Hover disabled; skipping step")
                elif action.type == ActionType.SWITCH_CONTEXT:
                    result = await self._execute_switch_context(action, result)
                # ── Expected outcome assertion for non-element actions
                if result.success and action.expected_outcome:
                    ok, outcome_msg = await self._check_expected_outcome(action.expected_outcome)
                    if not ok:
                        result.success = False
                        result.failure_reason = FailureReason.VALIDATION_FAILED
                        result.failure_message = f"Expected outcome not met: {outcome_msg}"
                        if self.config.screenshot_on_failure:
                            try:
                                _fname = f"outcome_failure_{action.id}.png"
                                screenshot_path = os.path.join(self.config.screenshots_dir, _fname) if self.config.screenshots_dir else _fname
                                await self._page.screenshot(path=screenshot_path)
                                result.screenshot_path = screenshot_path
                            except Exception:
                                pass
                        result.time_taken_ms = (time.time() - start_time) * 1000
                        self.logger.log_action_result(result)
                        return result
                # ── Stamp elapsed time (sub-methods don't have access to start_time)
                result.time_taken_ms = (time.time() - start_time) * 1000
                return result

            await self._wait_for_page_ready(action)

            # Phase 1-3: deterministic direct locator ladder.
            # Only used in deterministic_first replay mode (default).
            locator = None
            if self.config.replay_mode in ("deterministic_first", ""):
                locator = await self._resolve_locator_direct_first(action, attempt_trace)
            if locator:
                result.selection_source = "direct"
            else:
                # Phase 4: resolver fallback only after direct path fails.
                # Don't commit selection_source until we know if it succeeded.
                resolution, resolver_locator = await self._resolve_with_resolver_fallback(
                    action,
                    attempt_trace,
                )
                result.resolution = resolution
                if not resolution or not resolution.success or not resolver_locator:
                    result.selection_source = "none"  # nothing was resolved
                    result.failure_reason = (
                        resolution.failure_reason if resolution and resolution.failure_reason
                        else FailureReason.LOW_CONFIDENCE
                    )
                    result.failure_message = (
                        resolution.failure_message if resolution and resolution.failure_message
                        else "No candidates found matching target criteria"
                    )
                    result.time_taken_ms = (time.time() - start_time) * 1000
                    self.logger.log_action_result(result)
                    return result
                result.selection_source = "resolver"
                locator = resolver_locator

            # ── Group Selection: "Vary from Group" ──────────────────────
            if action.selection_rule and action.selection_rule.enabled and locator:
                try:
                    group_locator = await self._apply_selection_rule(
                        action, locator
                    )
                    if group_locator:
                        locator = group_locator
                        result.selection_source = "group"
                except Exception as ge:
                    if self.config.verbose:
                        print(f"  ⚠️ Group selection failed, using original: {ge}")

            # ── Precondition check (before the action fires so page state is not mutated)
            if action.preconditions:
                prec_ok, prec_msg = await self._check_preconditions(action.preconditions, locator)
                if not prec_ok:
                    result.failure_reason = FailureReason.STATE_BLOCKED
                    result.failure_message = f"Precondition failed: {prec_msg}"
                    result.time_taken_ms = (time.time() - start_time) * 1000
                    self.logger.log_action_result(result)
                    return result

            await self._execute_action_with_retry(action, locator, attempt_trace)

            result.success = True

            # ── Expected outcome assertion (post-action)
            if action.expected_outcome:
                ok, outcome_msg = await self._check_expected_outcome(action.expected_outcome)
                if not ok:
                    result.success = False
                    result.failure_reason = FailureReason.VALIDATION_FAILED
                    result.failure_message = f"Expected outcome not met: {outcome_msg}"
                    if self.config.screenshot_on_failure:
                        try:
                            _fname = f"outcome_failure_{action.id}.png"
                            screenshot_path = os.path.join(self.config.screenshots_dir, _fname) if self.config.screenshots_dir else _fname
                            await self._page.screenshot(path=screenshot_path)
                            result.screenshot_path = screenshot_path
                        except Exception:
                            pass
        except Exception as e:
            result.failure_reason = FailureReason.NOT_INTERACTABLE
            result.failure_message = str(e)
            # Screenshot on failure
            if self.config.screenshot_on_failure:
                try:
                    _fname = f"failure_action_{action.id}.png"
                    screenshot_path = os.path.join(self.config.screenshots_dir, _fname) if self.config.screenshots_dir else _fname
                    await self._page.screenshot(path=screenshot_path)
                    result.screenshot_path = screenshot_path
                except Exception:
                    pass
        
        result.time_taken_ms = (time.time() - start_time) * 1000
        self.logger.log_action_result(result)
        
        return result

    # ── Group Selection ("Vary from Group") ─────────────────────────
    # NOTE: _group_round_robin_counters is now an instance attribute (set in
    # __init__) so each Executor resets the counter between test runs.

    async def _apply_selection_rule(
        self, action: ActionNode, original_locator: Locator
    ) -> Optional[Locator]:
        """
        When a step has a SelectionRule, find all siblings in the
        repeating group and pick one according to the configured strategy.
        Returns a new Locator or None to keep the original.
        """
        import random as _rand

        rule = action.selection_rule
        if not rule or not rule.enabled:
            return None

        group_sel = rule.group_selector
        if not group_sel:
            return None

        siblings = self._page.locator(group_sel)
        count = await siblings.count()
        if count < 2:
            return None  # Not really a group

        strategy = rule.strategy or "round_robin"

        if strategy == "random":
            idx = _rand.randint(0, count - 1)
        elif strategy == "round_robin":
            key = f"{action.id}:{group_sel}"
            prev = self._group_round_robin_counters.get(key, -1)
            idx = (prev + 1) % count
            self._group_round_robin_counters[key] = idx
        elif strategy == "by_text":
            text_filter = (rule.text_filter or "").lower()
            idx = 0
            for i in range(count):
                el_text = (await siblings.nth(i).inner_text()).lower()
                if text_filter in el_text:
                    idx = i
                    break
        elif strategy == "exclude_previous":
            key = f"{action.id}:{group_sel}"
            prev = self._group_round_robin_counters.get(key, -1)
            candidates = [i for i in range(count) if i != prev]
            idx = _rand.choice(candidates) if candidates else 0
            self._group_round_robin_counters[key] = idx
        else:
            return None  # Unknown strategy

        if self.config.verbose:
            print(f"  🔄 Group selection: {strategy} → sibling {idx + 1}/{count}")

        return siblings.nth(idx)

    # ── Precondition & outcome assertion helpers ─────────────────────

    async def _check_preconditions(
        self, preconditions: Preconditions, locator: Optional["Locator"] = None
    ) -> tuple[bool, str]:
        """
        Verify preconditions against the live page before acting.
        Returns (ok, failure_message).
        """
        if preconditions.url_contains:
            current_url = self._page.url
            if preconditions.url_contains not in current_url:
                return False, (
                    f"URL does not contain '{preconditions.url_contains}' "
                    f"(current: {current_url})"
                )

        if preconditions.element_visible and locator is not None:
            try:
                visible = await locator.is_visible()
                if not visible:
                    return False, "Target element is not visible (required by precondition)"
            except Exception:
                pass  # Visibility check failed — skip enforcement

        if preconditions.element_enabled and locator is not None:
            try:
                enabled = await locator.is_enabled()
                if not enabled:
                    return False, "Target element is not enabled (required by precondition)"
            except Exception:
                pass  # Enabled check failed — skip enforcement

        if preconditions.modal_visible:
            # Check for any open dialog/modal
            dialogs = self._page.locator('[role="dialog"], [role="alertdialog"], dialog')
            try:
                count = await dialogs.count()
                if count == 0:
                    return False, "No modal/dialog is visible (required by precondition)"
            except Exception:
                pass

        return True, ""

    async def _check_expected_outcome(self, expected_outcome: dict) -> tuple[bool, str]:
        """
        Assert the expected outcome after an action.
        Returns (ok, failure_message).
        """
        outcome_type = expected_outcome.get("outcome_type")
        value = expected_outcome.get("value")

        if not outcome_type or outcome_type == "none":
            return True, ""

        # Give the page a moment to react (navigation, toast, DOM update)
        await asyncio.sleep(0.4)

        if outcome_type == "url_change":
            # Wait briefly for any navigation
            try:
                await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass
            current_url = self._page.url
            if value:
                if value not in current_url:
                    return False, f"URL does not contain '{value}' (current: {current_url})"
            # When no value specified, caller provides just a type hint — can't assert
            return True, ""

        if outcome_type == "element_appears":
            if not value:
                # No selector specified — outcome hint only, skip hard check
                return True, ""
            locator = self._page.locator(value)
            try:
                await locator.wait_for(state="visible", timeout=5000)
                return True, ""
            except Exception:
                return False, f"Element '{value}' did not appear within timeout"

        if outcome_type == "text_contains":
            if not value:
                return True, ""
            try:
                content = await self._page.content()
                if value.lower() not in content.lower():
                    return False, f"Page does not contain text '{value}'"
            except Exception:
                pass
            return True, ""

        return True, ""

    async def _execute_go_back(self, result: ActionResult) -> ActionResult:
        """Execute browser back navigation."""
        try:
            await self._page.go_back(wait_until="domcontentloaded")
            # Give the page time to fully render after navigation
            try:
                await self._page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass  # networkidle is best-effort
            result.success = True
            print(f"  Navigated back → {self._page.url}")
        except Exception as e:
            result.failure_reason = FailureReason.NAVIGATION_FAILED
            result.failure_message = str(e)
        self.logger.log_action_result(result)
        return result

    async def _execute_refresh(self, result: ActionResult) -> ActionResult:
        """Execute page refresh."""
        try:
            await self._page.reload(wait_until="domcontentloaded")
            # Give the page time to fully render after reload
            try:
                await self._page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass  # networkidle is best-effort
            result.success = True
            print(f"  Refreshed page → {self._page.url}")
        except Exception as e:
            result.failure_reason = FailureReason.NAVIGATION_FAILED
            result.failure_message = str(e)
        self.logger.log_action_result(result)
        return result

    async def _execute_wait_for_stable(self, result: ActionResult) -> ActionResult:
        """Wait for the page to reach a stable state (networkidle + DOM settle)."""
        try:
            try:
                await self._page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            # Brief additional settle for client-side frameworks
            import asyncio
            await asyncio.sleep(0.5)
            result.success = True
            print("  Waited for page stability")
        except Exception as e:
            result.failure_reason = FailureReason.NAVIGATION_FAILED
            result.failure_message = str(e)
        self.logger.log_action_result(result)
        return result

    async def _execute_switch_context(
        self,
        action: ActionNode,
        result: ActionResult,
    ) -> ActionResult:
        """Switch executor focus to the context encoded in the action."""
        try:
            if not self._page or self._page.is_closed():
                result.failure_reason = FailureReason.CONTEXT_CONFLICT
                result.failure_message = "No active browser context is available to switch into."
                self.logger.log_action_result(result)
                return result
            result.success = True
            active = self._active_context_id or "unknown"
            current_url = self._page.url if self._page else ""
            print(f"  Switched context → {active} ({current_url[:80]})")
        except Exception as e:
            result.failure_reason = FailureReason.CONTEXT_CONFLICT
            result.failure_message = str(e)
        self.logger.log_action_result(result)
        return result
    
    async def _execute_navigate(
        self,
        action: ActionNode,
        result: ActionResult,
    ) -> ActionResult:
        """Execute a navigation action."""
        url = action.target.url
        if not url:
            result.failure_reason = FailureReason.NAVIGATION_FAILED
            result.failure_message = "No URL provided for navigate action"
            return result
        
        try:
            await self._page.goto(url, wait_until="domcontentloaded")
            # Best-effort networkidle wait; don't fail if analytics keep requests open
            try:
                await self._page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            result.success = True
            print(f"  Navigated to: {url}")
        except Exception as e:
            result.failure_reason = FailureReason.NAVIGATION_FAILED
            result.failure_message = str(e)

        self.logger.log_action_result(result)
        return result
    
    async def _execute_wait(
        self,
        action: ActionNode,
        result: ActionResult,
    ) -> ActionResult:
        """Execute a wait action."""
        # Default wait is 1 second
        wait_ms = int(action.value or 1000) if action.value else 1000
        
        await asyncio.sleep(wait_ms / 1000)
        result.success = True
        print(f"  Waited {wait_ms}ms")
        
        self.logger.log_action_result(result)
        return result
    
    async def _execute_hover(self, locator: Locator) -> None:
        """Execute a hover action to reveal hidden UI (menus, tooltips, dropdowns)."""
        await locator.hover()
        # Allow CSS transitions / JS to show the hover-gated content
        await asyncio.sleep(0.4)
    
    async def _execute_click(self, locator: Locator) -> None:
        """Execute a click action. Handles hover-gated elements and pointer interception."""
        try:
            # Click and handle possible navigation
            await locator.click()
        except Exception as e:
            err_msg = str(e)
            # If click triggered a navigation, the execution context may be destroyed
            if "Execution context was destroyed" in err_msg or "Target closed" in err_msg:
                # Navigation happened — wait for it to settle
                try:
                    await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass
                return
            
            # If another element intercepts pointer events, the target is likely
            # behind a hover-gated overlay. Try hovering to reveal it, then retry.
            if "intercepts pointer events" in err_msg:
                # Attempt 1: hover the element itself to trigger ancestor :hover CSS
                try:
                    await locator.hover(force=True)
                    await asyncio.sleep(0.5)  # Wait for CSS transition
                    await locator.click()
                    await asyncio.sleep(ACTION_DELAY / 1000)
                    try:
                        await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except Exception:
                        pass
                    return
                except Exception:
                    pass
                
                # Attempt 2: scroll element to viewport center to avoid header overlap
                try:
                    await locator.evaluate(
                        "el => el.scrollIntoView({block: 'center', behavior: 'instant'})"
                    )
                    await asyncio.sleep(0.3)
                    await locator.click()
                    await asyncio.sleep(ACTION_DELAY / 1000)
                    try:
                        await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except Exception:
                        pass
                    return
                except Exception:
                    pass
                
                # Attempt 3: force click (bypasses actionability checks)
                try:
                    await locator.click(force=True)
                    await asyncio.sleep(ACTION_DELAY / 1000)
                    try:
                        await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except Exception:
                        pass
                    return
                except Exception as force_err:
                    if "Execution context was destroyed" in str(force_err) or "Target closed" in str(force_err):
                        try:
                            await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
                        except Exception:
                            pass
                        return
                    # Fall through to Attempt 4

                # Attempt 4: dispatch_event — fires the DOM click event directly,
                # bypassing ALL of Playwright's pointer-event and visibility checks.
                # This handles Bootstrap/MUI modals and other overlay interceptors
                # that legitimately sit in the z-stack above the trigger button.
                try:
                    await locator.dispatch_event("click")
                    await asyncio.sleep(ACTION_DELAY / 1000)
                    try:
                        await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                    return
                except Exception as dispatch_err:
                    if "Execution context was destroyed" in str(dispatch_err) or "Target closed" in str(dispatch_err):
                        try:
                            await self._page.wait_for_load_state("domcontentloaded", timeout=5000)
                        except Exception:
                            pass
                        return
                    raise

            raise
        # Brief delay for UI to settle
        await asyncio.sleep(ACTION_DELAY / 1000)
        # Wait for any navigation triggered by the click
        try:
            await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:
            pass
    
    async def _execute_type(self, locator: Locator, value: str) -> None:
        """Execute a type action."""
        await locator.fill(value)
        await asyncio.sleep(ACTION_DELAY / 1000)
    
    async def _execute_select(self, locator: Locator, value: str) -> None:
        """Execute a select (dropdown) action."""
        normalized_value = (value or "").strip()
        option_snapshot = []
        try:
            option_snapshot = await locator.evaluate(
                """el => Array.from((el && el.options) || []).map((o, i) => ({
                    index: i,
                    value: String(o.value || ""),
                    label: String((o.label || o.textContent || "")).trim(),
                }))"""
            )
        except Exception:
            option_snapshot = []

        if option_snapshot:
            by_value = next((o for o in option_snapshot if o["value"] == normalized_value), None)
            if by_value:
                await locator.select_option(value=normalized_value)
                await asyncio.sleep(ACTION_DELAY / 1000)
                return

            by_label = next((o for o in option_snapshot if o["label"] == normalized_value), None)
            if by_label:
                await locator.select_option(label=normalized_value)
                await asyncio.sleep(ACTION_DELAY / 1000)
                return

            if normalized_value.isdigit():
                idx = int(normalized_value)
                if 0 <= idx < len(option_snapshot):
                    await locator.select_option(index=idx)
                    await asyncio.sleep(ACTION_DELAY / 1000)
                    return

            raise ValueError(
                f"Could not select option '{value}' (no exact value/label/index match)"
            )

        try:
            await locator.select_option(value=normalized_value)
        except Exception:
            try:
                await locator.select_option(label=normalized_value)
            except Exception:
                try:
                    idx = int(normalized_value)
                    await locator.select_option(index=idx)
                except (ValueError, Exception):
                    raise ValueError(f"Could not select option '{value}' by value, label, or index")
        await asyncio.sleep(ACTION_DELAY / 1000)

    async def _execute_submit(self, locator: Locator) -> None:
        """Execute a form submit action."""
        async def _wait_submit_navigation() -> None:
            try:
                await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
            except Exception:
                pass

        try:
            tag = await locator.evaluate("el => (el.tagName || '').toLowerCase()")
        except Exception:
            tag = ""

        if tag == "form":
            try:
                await locator.evaluate("form => form.requestSubmit()")
            except Exception as e:
                if "Execution context was destroyed" in str(e) or "Target closed" in str(e):
                    await _wait_submit_navigation()
                    return
                try:
                    await locator.evaluate("form => form.submit()")
                except Exception as e2:
                    if "Execution context was destroyed" in str(e2) or "Target closed" in str(e2):
                        await _wait_submit_navigation()
                        return
                    raise
            await asyncio.sleep(ACTION_DELAY / 1000)
            await _wait_submit_navigation()
            return

        try:
            await locator.press("Enter")
        except Exception:
            await locator.click()
        await asyncio.sleep(ACTION_DELAY / 1000)
        await _wait_submit_navigation()
    
    async def _execute_keypress(self, locator: Locator, key: str) -> None:
        """Execute a keypress action (Enter for submit, Tab for focus shift)."""
        await locator.press(key)
        await asyncio.sleep(ACTION_DELAY / 1000)
        # If Enter was pressed, it may trigger navigation
        if key == "Enter":
            try:
                await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
            except Exception:
                pass
    
    async def _wait_for_page_ready(self, action: ActionNode) -> None:
        """
        Wait for the page to be ready for interaction.
        
        For SPAs the DOM might exist (domcontentloaded) but React/Vue
        hasn't hydrated yet.  We use a targeted wait for the element
        we're looking for, with short timeouts to avoid burning retry budget.
        """
        # 1. Ensure at least domcontentloaded
        try:
            await self._page.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:
            pass
        
        # 2. Try to wait for an element matching the target to appear
        if action.target:
            hint_selector = self._build_hint_selector(action)
            if hint_selector:
                try:
                    await self._page.wait_for_selector(
                        hint_selector, state="attached", timeout=3000,
                    )
                    # Brief settle for React render cycle
                    await asyncio.sleep(0.2)
                    return
                except Exception:
                    pass  # Fall through to generic wait
        
        # 3. Generic settle: short networkidle wait
        try:
            await self._page.wait_for_load_state("networkidle", timeout=2000)
        except Exception:
            pass
        await asyncio.sleep(0.3)
    
    def _build_hint_selector(self, action: ActionNode) -> Optional[str]:
        """
        Build a lightweight CSS selector hint we can use with
        page.wait_for_selector() to know the target is in the DOM.
        
        Priority: simple stable selectors FIRST, full CSS as fallback.
        The recorded CSS is often extremely specific (Tailwind class chains)
        and fails during SPA hydration. Simple selectors match faster.
        """
        target = action.target
        if not target:
            return None
        
        # 1. Snapshot attributes — simple, stable selectors
        if target.element_snapshot:
            snap = target.element_snapshot
            tag = snap.tag or "*"
            
            if snap.attributes:
                # Try id (most stable)
                if snap.attributes.get("id"):
                    return f"#{snap.attributes['id']}"
                # Try data-testid
                for tid_attr in ("data-testid", "data-test-id", "data-cy"):
                    if snap.attributes.get(tid_attr):
                        return f'[{tid_attr}="{snap.attributes[tid_attr]}"]'
                # Try name
                if snap.attributes.get("name"):
                    return f'{tag}[name="{snap.attributes["name"]}"]'
                # Try placeholder
                if snap.attributes.get("placeholder"):
                    ph = snap.attributes["placeholder"].replace('"', '\\"')
                    return f'{tag}[placeholder="{ph}"]'
            
            # Try role
            if snap.role:
                escaped_role = snap.role.replace('"', '\\"')
                return f'{tag}[role="{escaped_role}"]'
        
        # 2. Role from target
        if target.role:
            tag = target.element_snapshot.tag if target.element_snapshot else "*"
            return f'{tag}[role="{target.role}"]'
        
        # 3. Recorded CSS as last resort (fragile but better than nothing)
        if target.selectors and target.selectors.css:
            return target.selectors.css
        
        return None

    @staticmethod
    def _escape_attr_value(value: str) -> str:
        return str(value).replace("\\", "\\\\").replace("'", "\\'")

    @staticmethod
    def _collect_target_names(action: ActionNode) -> list[str]:
        names: list[str] = []
        target = action.target
        if not target:
            return names

        for value in (
            target.label,
            target.friendly_name,
            (target.element_snapshot.text if target.element_snapshot else None),
            (target.element_snapshot.aria_label if target.element_snapshot else None),
            (target.element_snapshot.attributes or {}).get("placeholder")
            if target.element_snapshot and target.element_snapshot.attributes
            else None,
        ):
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned and cleaned not in names:
                    names.append(cleaned)

        for value in target.semantic_text or []:
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned and len(cleaned) > 1 and cleaned not in names:
                    names.append(cleaned)
        return names

    @staticmethod
    def _record_attempt(
        attempt_trace: list[dict[str, Any]],
        *,
        phase: str,
        strategy: str,
        status: str,
        detail: Optional[dict[str, Any]] = None,
    ) -> None:
        payload: dict[str, Any] = {
            "phase": phase,
            "strategy": strategy,
            "status": status,
            "ts": time.time(),
        }
        if detail:
            payload.update(detail)
        attempt_trace.append(payload)

    async def _try_unique_locator(
        self,
        locator: Locator,
        *,
        phase: str,
        strategy: str,
        attempt_trace: list[dict[str, Any]],
        selector_hint: Optional[str] = None,
    ) -> Optional[Locator]:
        try:
            count = await locator.count()
            status = "match" if count == 1 else ("ambiguous" if count > 1 else "miss")
            self._record_attempt(
                attempt_trace,
                phase=phase,
                strategy=strategy,
                status=status,
                detail={"count": count, "selector": selector_hint},
            )
            if count == 1:
                return locator.first
            return None
        except Exception as exc:
            self._record_attempt(
                attempt_trace,
                phase=phase,
                strategy=strategy,
                status="error",
                detail={"selector": selector_hint, "error": str(exc)},
            )
            return None

    async def _try_direct_strict_locators(
        self,
        action: ActionNode,
        attempt_trace: list[dict[str, Any]],
        *,
        phase: str,
    ) -> Optional[Locator]:
        target = action.target
        if not target:
            return None

        selectors = target.selectors
        snapshot_attrs = (target.element_snapshot.attributes or {}) if target.element_snapshot else {}
        tag = (target.element_snapshot.tag or "").strip() if target.element_snapshot else ""

        test_id = None
        if selectors and selectors.test_id:
            test_id = selectors.test_id
        if not test_id:
            test_id = (
                snapshot_attrs.get("data-testid")
                or snapshot_attrs.get("data-test-id")
                or snapshot_attrs.get("data-cy")
            )
        if test_id:
            locator = await self._try_unique_locator(
                self._page.get_by_test_id(test_id),
                phase=phase,
                strategy="test_id",
                attempt_trace=attempt_trace,
                selector_hint=f"test_id={test_id}",
            )
            if locator:
                return locator

        if snapshot_attrs.get("id"):
            escaped = self._escape_attr_value(snapshot_attrs["id"])
            locator = await self._try_unique_locator(
                self._page.locator(f"[id='{escaped}']"),
                phase=phase,
                strategy="id",
                attempt_trace=attempt_trace,
                selector_hint=f"id={snapshot_attrs['id']}",
            )
            if locator:
                return locator

        if snapshot_attrs.get("name"):
            escaped = self._escape_attr_value(snapshot_attrs["name"])
            prefix = f"{tag}" if tag else ""
            locator = await self._try_unique_locator(
                self._page.locator(f"{prefix}[name='{escaped}']" if prefix else f"[name='{escaped}']"),
                phase=phase,
                strategy="name",
                attempt_trace=attempt_trace,
                selector_hint=f"name={snapshot_attrs['name']}",
            )
            if locator:
                return locator

        aria_label = snapshot_attrs.get("aria-label") or (
            target.element_snapshot.aria_label if target.element_snapshot else None
        )
        if aria_label:
            escaped = self._escape_attr_value(aria_label)
            locator = await self._try_unique_locator(
                self._page.locator(f"[aria-label='{escaped}']"),
                phase=phase,
                strategy="aria_label",
                attempt_trace=attempt_trace,
                selector_hint=f"aria-label={aria_label}",
            )
            if locator:
                return locator

        if selectors and selectors.css:
            locator = await self._try_unique_locator(
                self._page.locator(selectors.css),
                phase=phase,
                strategy="recorded_css",
                attempt_trace=attempt_trace,
                selector_hint=selectors.css,
            )
            if locator:
                return locator

        if selectors and selectors.xpath:
            locator = await self._try_unique_locator(
                self._page.locator(f"xpath={selectors.xpath}"),
                phase=phase,
                strategy="recorded_xpath",
                attempt_trace=attempt_trace,
                selector_hint=selectors.xpath,
            )
            if locator:
                return locator

        return None

    async def _try_selector_bundle_locators(
        self,
        action: ActionNode,
        attempt_trace: list[dict[str, Any]],
        *,
        phase: str,
    ) -> Optional[Locator]:
        target = action.target
        if not target:
            return None

        names = self._collect_target_names(action)
        snapshot_attrs = (target.element_snapshot.attributes or {}) if target.element_snapshot else {}
        tag = (target.element_snapshot.tag or "").strip() if target.element_snapshot else ""

        role = target.role or (target.element_snapshot.role if target.element_snapshot else None)
        if role:
            role_name = self.TAG_TO_ROLE.get(role.lower(), role.lower())
            for candidate_name in names[:3]:
                locator = await self._try_unique_locator(
                    self._page.get_by_role(role_name, name=candidate_name),
                    phase=phase,
                    strategy="role_name",
                    attempt_trace=attempt_trace,
                    selector_hint=f"role={role_name}, name={candidate_name}",
                )
                if locator:
                    return locator

        placeholder = snapshot_attrs.get("placeholder")
        if placeholder:
            locator = await self._try_unique_locator(
                self._page.get_by_placeholder(placeholder),
                phase=phase,
                strategy="placeholder",
                attempt_trace=attempt_trace,
                selector_hint=f"placeholder={placeholder}",
            )
            if locator:
                return locator

        if snapshot_attrs.get("type") and tag.lower() == "input":
            escaped_type = self._escape_attr_value(snapshot_attrs["type"])
            locator = await self._try_unique_locator(
                self._page.locator(f"input[type='{escaped_type}']"),
                phase=phase,
                strategy="input_type",
                attempt_trace=attempt_trace,
                selector_hint=f"input[type={snapshot_attrs['type']}]",
            )
            if locator:
                return locator

        for candidate_name in names[:2]:
            if len(candidate_name) > 120:
                continue
            locator = await self._try_unique_locator(
                self._page.get_by_text(candidate_name, exact=True),
                phase=phase,
                strategy="exact_text",
                attempt_trace=attempt_trace,
                selector_hint=candidate_name,
            )
            if locator:
                return locator

        return None

    async def _resolve_locator_direct_first(
        self,
        action: ActionNode,
        attempt_trace: list[dict[str, Any]],
    ) -> Optional[Locator]:
        locator = await self._try_direct_strict_locators(
            action,
            attempt_trace,
            phase="direct_strict",
        )
        if locator:
            return locator

        for attempt in range(1, MAX_DIRECT_RECOVERY_ATTEMPTS + 1):
            self._record_attempt(
                attempt_trace,
                phase="direct_recovery",
                strategy="retry_wait",
                status="retry",
                detail={"attempt": attempt},
            )
            await asyncio.sleep(0.2 * attempt)
            await self._wait_for_page_ready(action)

            # Re-scroll to recorded y-position for viewport-sensitive UIs.
            if action.target and action.target.element_snapshot:
                bbox = action.target.element_snapshot.bounding_box or {}
                if isinstance(bbox, dict) and bbox.get("y", 0) > 0:
                    try:
                        await self._page.evaluate(
                            "y => window.scrollTo({top: Math.max(0, y - 200), behavior: 'instant'})",
                            bbox["y"],
                        )
                    except Exception:
                        pass

            locator = await self._try_direct_strict_locators(
                action,
                attempt_trace,
                phase=f"direct_recovery_{attempt}",
            )
            if locator:
                return locator

        return await self._try_selector_bundle_locators(
            action,
            attempt_trace,
            phase="direct_bundle",
        )

    @staticmethod
    def _is_transient_action_error(error: Exception) -> bool:
        text = str(error).lower()
        return any(token in text for token in TRANSIENT_ACTION_ERROR_TOKENS)

    async def _execute_action_with_retry(
        self,
        action: ActionNode,
        locator: Locator,
        attempt_trace: list[dict[str, Any]],
    ) -> None:
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                if action.type == ActionType.CLICK:
                    await self._execute_click(locator)
                elif action.type == ActionType.TYPE:
                    await self._execute_type(locator, action.value or "")
                elif action.type == ActionType.SELECT:
                    await self._execute_select(locator, action.value or "")
                elif action.type == ActionType.SUBMIT:
                    await self._execute_submit(locator)
                elif action.type == ActionType.KEYPRESS:
                    await self._execute_keypress(locator, action.value or "Enter")

                self._record_attempt(
                    attempt_trace,
                    phase="execute",
                    strategy=action.type.value,
                    status="success",
                    detail={"attempt": attempt},
                )
                return
            except Exception as exc:
                transient = self._is_transient_action_error(exc)
                self._record_attempt(
                    attempt_trace,
                    phase="execute",
                    strategy=action.type.value,
                    status="error",
                    detail={
                        "attempt": attempt,
                        "transient": transient,
                        "error": str(exc),
                    },
                )
                if not transient or attempt >= max_attempts:
                    raise
                await asyncio.sleep(0.25 * attempt)
                try:
                    await locator.scroll_into_view_if_needed(timeout=1000)
                except Exception:
                    pass

    def _resolver_medium_invariants_pass(
        self,
        action: ActionNode,
        resolution: ResolutionResult,
    ) -> tuple[bool, list[str]]:
        issues: list[str] = []
        target = action.target
        selected = resolution.selected_element
        selected_candidate = resolution.selected_candidate
        if not target or not selected:
            return False, ["missing_target_or_selected_element"]

        snapshot = target.element_snapshot
        if snapshot and snapshot.tag and selected.tag and snapshot.tag.lower() != selected.tag.lower():
            issues.append("tag_mismatch")

        expected_role = (target.role or (snapshot.role if snapshot else None) or "").strip().lower()
        selected_role = (selected.role or "").strip().lower()
        if expected_role and selected_role and expected_role != selected_role:
            issues.append("role_mismatch")

        context_tags: list[str] = []
        for node in target.context_path or []:
            if isinstance(node, str):
                value = node.strip().lower()
                if value:
                    context_tags.append(value)
            elif isinstance(node, dict):
                value = str(node.get("tag") or "").strip().lower()
                if value:
                    context_tags.append(value)
        if context_tags:
            target_set = set(context_tags)
            selected_set = {
                str(anc.get("tag") or "").strip().lower()
                for anc in (selected.ancestors or [])
                if isinstance(anc, dict)
            }
            overlap_ratio = (len(target_set.intersection(selected_set)) / max(len(target_set), 1))
            if overlap_ratio < 0.34:
                issues.append("low_context_overlap")

        selected_attrs = selected.attributes or {}
        snapshot_attrs = (snapshot.attributes or {}) if snapshot else {}
        durable_anchor = any(
            [
                selected.matches_recorded_selector,
                bool(target.test_id and (
                    selected_attrs.get("data-testid") == target.test_id
                    or selected_attrs.get("data-test-id") == target.test_id
                    or selected_attrs.get("data-cy") == target.test_id
                )),
                bool(snapshot_attrs.get("id") and selected_attrs.get("id") == snapshot_attrs.get("id")),
                bool(snapshot_attrs.get("name") and selected_attrs.get("name") == snapshot_attrs.get("name")),
            ]
        )
        strong_structure = bool(
            (
                target.index is not None
                and selected.sibling_index == target.index
            )
            or (selected_candidate and selected_candidate.selector_score >= 0.8)
        )

        if not durable_anchor and not strong_structure:
            # For moderate / aggressive / flexible generalization the absence of a
            # durable anchor is expected — targets like YouTube results, search
            # listings and dynamic cards have no stable test-id, id or selector.
            # Accept the match when the combined score clears the medium threshold.
            _LENIENT_GEN = {
                GeneralizationLevel.ANY_MATCHING,
                GeneralizationLevel.MODERATE,
                GeneralizationLevel.AGGRESSIVE,
                GeneralizationLevel.FLEXIBLE,
            }
            _score = selected_candidate.score if selected_candidate else 0.0
            if action.generalization in _LENIENT_GEN and _score >= 0.45:
                pass  # Allowed: good-enough score in lenient generalization mode
            else:
                issues.append("missing_durable_anchor_or_structure")

        return len(issues) == 0, issues

    async def _resolve_with_resolver_fallback(
        self,
        action: ActionNode,
        attempt_trace: list[dict[str, Any]],
    ) -> tuple[Optional[ResolutionResult], Optional[Locator]]:
        last_resolution: Optional[ResolutionResult] = None
        last_signature: Optional[tuple[Any, ...]] = None

        for attempt in range(1, MAX_RESOLVER_ATTEMPTS + 1):
            await self._wait_for_page_ready(action)
            candidates = await self._extract_dom_elements(action)
            self.router.set_dom_lookup(candidates)
            context = {"current_url": self._page.url}

            resolution = self.router.resolve(
                candidates,
                action,
                context,
                verbose=(attempt == 1),
            )
            last_resolution = resolution
            self._record_attempt(
                attempt_trace,
                phase="resolver",
                strategy="router",
                status="success" if resolution.success else "failed",
                detail={
                    "attempt": attempt,
                    "confidence_band": resolution.confidence_band,
                    "failure_reason": resolution.failure_reason.value if resolution.failure_reason else None,
                    "semantic_candidates": resolution.semantic_candidates_count,
                    "context_candidates": resolution.context_filtered_count,
                    "affordance_candidates": resolution.affordance_passed_count,
                },
            )

            if resolution.success:
                if resolution.confidence_band == "low":
                    # Under 'permissive' policy, allow low confidence through
                    if self.config.resolver_fallback_policy == "permissive":
                        pass  # Allow low confidence
                    else:
                        resolution.success = False
                        resolution.failure_reason = FailureReason.LOW_CONFIDENCE
                        resolution.failure_message = "Low confidence resolver selection blocked by policy"
                elif resolution.confidence_band == "medium":
                    # Under 'strict' policy, reject medium confidence too
                    if self.config.resolver_fallback_policy == "strict":
                        resolution.success = False
                        resolution.failure_reason = FailureReason.LOW_CONFIDENCE
                        resolution.failure_message = "Medium confidence blocked by strict resolver policy"
                    else:
                        ok, issues = self._resolver_medium_invariants_pass(action, resolution)
                        if not ok:
                            resolution.success = False
                            resolution.failure_reason = FailureReason.LOW_CONFIDENCE
                            resolution.failure_message = (
                                "Medium-confidence resolver selection failed invariants: "
                                + ", ".join(issues)
                            )
                            self._record_attempt(
                                attempt_trace,
                                phase="resolver_guard",
                                strategy="medium_invariants",
                                status="failed",
                                detail={"issues": issues},
                            )
                        else:
                            self._record_attempt(
                                attempt_trace,
                                phase="resolver_guard",
                                strategy="medium_invariants",
                                status="passed",
                            )

            if resolution.success:
                self.logger.log_resolution(resolution)
                locator = await self._get_locator(resolution.selected_element, action)
                if locator:
                    return resolution, locator
                resolution.success = False
                resolution.failure_reason = FailureReason.SELECTOR_NO_MATCH
                resolution.failure_message = "Could not create locator for resolver-selected element"

            reason_value = resolution.failure_reason.value if resolution.failure_reason else None
            signature = (
                reason_value,
                resolution.semantic_candidates_count,
                resolution.context_filtered_count,
                resolution.affordance_passed_count,
            )

            stable_ambiguity = (
                reason_value in {"low_confidence", "semantic_ambiguity", "selector_no_match"}
                and signature == last_signature
            )
            if stable_ambiguity:
                break

            last_signature = signature
            if attempt < MAX_RESOLVER_ATTEMPTS:
                await asyncio.sleep(0.3 * attempt)

        if last_resolution and (not last_resolution.success):
            self.logger.log_resolution(last_resolution)

        # ── iFrame fallback ─────────────────────────────────────────────────────────
        # Main frame exhausted all attempts.  Probe accessible child frames:
        # same-origin frames get the full DOM extractor JS; cross-origin frames
        # are logged and skipped (browser blocks JS execution there).
        #
        # Every element extracted from a child frame is tagged with
        # __frame_index so _get_locator() routes through the correct frame.
        if not last_resolution or not last_resolution.success:
            child_frames = self._page.frames[1:]  # index 0 is always the main frame
            if child_frames:
                frame_candidates: list[DOMElement] = []
                for f_idx, child_frame in enumerate(child_frames, start=1):
                    # Pass action=None: the recorded CSS/XPath selectors target
                    # the main frame and must not be evaluated inside child frames
                    # (they'd produce false matches_recorded_selector flags).
                    frame_elements = await self._extract_from_frame(child_frame, f_idx, action=None)
                    frame_candidates.extend(frame_elements)

                if frame_candidates:
                    print(
                        f"  [frame] Main frame resolution failed; probing "
                        f"{len(child_frames)} child frame(s) — "
                        f"{len(frame_candidates)} elements found"
                    )
                    self.router.set_dom_lookup(frame_candidates)
                    context = {"current_url": self._page.url}
                    frame_resolution = self.router.resolve(
                        frame_candidates, action, context, verbose=True
                    )
                    if frame_resolution.success:
                        self._record_attempt(
                            attempt_trace,
                            phase="resolver",
                            strategy="iframe_fallback",
                            status="success",
                            detail={"frame_count": len(child_frames)},
                        )
                        self.logger.log_resolution(frame_resolution)
                        locator = await self._get_locator(frame_resolution.selected_element, action)
                        if locator:
                            return frame_resolution, locator

        return last_resolution, None

    async def _extract_from_frame(
        self,
        frame,
        frame_index: int,
        action: Optional[ActionNode] = None,
    ) -> List[DOMElement]:
        """Extract interactive DOM elements from a child frame.

        Delegates to `_extract_dom_elements` with the frame as the root so
        the same JS extractor runs inside the frame context.
        Every returned DOMElement is tagged with ``__frame_index`` and
        ``__frame_url`` so that ``_get_locator`` routes interactions through
        the correct frame and can recover if the frame list shifts.

        Note: Playwright's ``evaluate()`` runs at the browser-process level and
        therefore works on both same-origin and cross-origin frames in
        controlled browsers.  Errors are still caught (e.g. detached frame,
        about:blank) and result in an empty list.
        """
        try:
            elements = await self._extract_dom_elements(action, _frame_root=frame)
            frame_url = frame.url  # fingerprint for staleness check at locate time
            for el in elements:
                el.attributes["__frame_index"] = str(frame_index)
                el.attributes["__frame_url"] = frame_url
            return elements
        except Exception:
            # Cross-origin or other access error — skip silently
            return []

    async def _extract_dom_elements(self, action: Optional[ActionNode] = None, _frame_root=None) -> List[DOMElement]:
        """
        Extract interactive elements from the DOM.
        
        Returns a list of DOMElement objects.
        """
        # Get recorded CSS selector if available
        recorded_css = None
        recorded_xpath = None
        if action and action.target and action.target.selectors and action.target.selectors.css:
            recorded_css = action.target.selectors.css
        if action and action.target and action.target.selectors and action.target.selectors.xpath:
            recorded_xpath = action.target.selectors.xpath
            
        js_code = """
        async (recorded) => {
            const elements = [];
            const recordedCss = recorded ? recorded.css : null;
            const recordedXpath = recorded ? recorded.xpath : null;
            const interactiveSelector = 'button, a, input, select, textarea, form, [role="button"], [role="link"], [role="checkbox"], [role="radio"], [role="textbox"], [role="menuitem"], [role="tab"], [tabindex], [onclick]';
            
            // Build a universal node registry for parent_id linkage
            const allInteractive = Array.from(document.querySelectorAll(interactiveSelector));
            const nodeRegistry = new Map();  // DOM element -> node_id
            allInteractive.forEach((el, index) => {
                nodeRegistry.set(el, `node_${index}`);
            });
            
            // Normalize text consistently with Python side:
            // lowercase, collapse whitespace, remove punctuation
            function normalizeText(text) {
                if (!text) return '';
                return text.toLowerCase()
                    .replace(/[^\\w\\s]/g, '')  // remove punctuation
                    .replace(/\\s+/g, ' ')
                    .trim();
            }
            
            allInteractive.forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                
                // Determine visibility — include hidden elements but flag them
                // so the resolver can see hover-gated content
                const isHidden = (style.display === 'none' || style.visibility === 'hidden');
                const isZeroRect = (rect.width === 0 && rect.height === 0);
                const isVisible = !isHidden && !isZeroRect;
                
                // Get all attributes
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                
                // Check if matches recorded CSS
                let matchesRecorded = false;
                if (recordedCss) {
                    try {
                        if (el.matches(recordedCss)) {
                            matchesRecorded = true;
                        }
                    } catch (e) {
                        // Ignore invalid selectors
                    }
                }
                if (!matchesRecorded && recordedXpath) {
                    try {
                        const xpathResult = document.evaluate(
                            recordedXpath,
                            document,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );
                        for (let i = 0; i < xpathResult.snapshotLength; i++) {
                            if (xpathResult.snapshotItem(i) === el) {
                                matchesRecorded = true;
                                break;
                            }
                        }
                    } catch (e) {
                        // Ignore invalid XPath
                    }
                }
                
                // Compute parent_id: find nearest ancestor that is interactive
                let parentId = null;
                let p = el.parentElement;
                while (p && p.tagName !== 'BODY') {
                    if (nodeRegistry.has(p)) {
                        parentId = nodeRegistry.get(p);
                        break;
                    }
                    p = p.parentElement;
                }
                
                // Compute sibling_index: position among same-tag siblings 
                // under the same direct parent
                let siblingIndex = -1;
                let siblingCount = 0;
                if (el.parentElement) {
                    const parentEl = el.parentElement;
                    const sameTagSiblings = Array.from(
                        parentEl.querySelectorAll(':scope > ' + el.tagName.toLowerCase())
                    );
                    siblingCount = sameTagSiblings.length;
                    siblingIndex = sameTagSiblings.indexOf(el);
                }
                
                // Get raw text and limit length for containers
                let rawText = el.innerText || el.textContent || '';
                // Truncate container text to avoid noise from descendant text
                if (rawText.length > 200 && !['input', 'textarea', 'button', 'a', 'select'].includes(el.tagName.toLowerCase())) {
                    rawText = rawText.substring(0, 200);
                }
                
                // Explicit role: only use getAttribute, don't default to tag
                const explicitRole = el.getAttribute('role');
                
                elements.push({
                    node_id: `node_${index}`,
                    tag: el.tagName.toLowerCase(),
                    text: rawText,
                    normalized_text: normalizeText(rawText),
                    role: explicitRole || null,
                    aria_label: el.getAttribute('aria-label'),
                    attributes: attrs,
                    is_visible: isVisible,
                    is_enabled: !el.disabled,
                    is_focusable: el.tabIndex >= 0 || ['input', 'select', 'textarea', 'button', 'a'].includes(el.tagName.toLowerCase()),
                    has_click_handler: el.onclick !== null || attrs['onclick'] !== undefined || style.cursor === 'pointer',
                    bounding_box: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    parent_id: parentId,
                    sibling_index: siblingIndex,
                    sibling_count: siblingCount,
                    ancestors: (() => {
                        const chain = [];
                        let p = el.parentElement;
                        while (p && p.tagName !== 'BODY' && chain.length < 10) {
                            // Capture rich attribute set for context resolver
                            const ancestorAttrs = {};
                            for (const attr of p.attributes) {
                                if (attr.name.startsWith('data-') || 
                                    attr.name === 'class' || 
                                    attr.name === 'id' ||
                                    attr.name.startsWith('aria-')) {
                                    ancestorAttrs[attr.name] = attr.value;
                                }
                            }
                            chain.push({
                                tag: p.tagName.toLowerCase(),
                                role: p.getAttribute('role') || null,
                                id: p.id,
                                attributes: ancestorAttrs
                            });
                            p = p.parentElement;
                        }
                        return chain;
                    })(),
                    matches_recorded_selector: matchesRecorded,
                    nearby_text: (() => {
                        // Walk up to the nearest row/card/list-item container
                        // and capture its text content for disambiguation of
                        // repeated identical elements (e.g. delete buttons in a list).
                        const containerTags = new Set(['tr', 'li', 'article', 'fieldset']);
                        const containerRoles = new Set(['row', 'listitem', 'group']);
                        let ancestor = el.parentElement;
                        let depth = 0;
                        while (ancestor && ancestor.tagName !== 'BODY' && depth < 6) {
                            const tag = ancestor.tagName.toLowerCase();
                            const role = ancestor.getAttribute('role');
                            const isCard = ancestor.classList && (
                                ancestor.classList.contains('card') ||
                                ancestor.classList.contains('item') ||
                                ancestor.classList.contains('row')
                            );
                            if (containerTags.has(tag) || containerRoles.has(role) || isCard) {
                                // Get text but exclude deeply nested interactive elements
                                let txt = (ancestor.innerText || '').replace(/[\\n\\r]+/g, ' ').trim();
                                if (txt.length > 200) txt = txt.substring(0, 200);
                                return txt;
                            }
                            ancestor = ancestor.parentElement;
                            depth++;
                        }
                        return '';
                    })()
                });
            });
            
            return elements;
        }
        """
        
        raw_elements = await (_frame_root or self._page).evaluate(
            js_code,
            {"css": recorded_css, "xpath": recorded_xpath},
        )
        
        # Convert to DOMElement objects
        elements = []
        for raw in raw_elements:
            element = DOMElement(
                node_id=raw["node_id"],
                tag=raw["tag"],
                text=raw["text"],
                normalized_text=raw["normalized_text"],
                role=raw["role"],
                aria_label=raw.get("aria_label"),
                attributes=raw.get("attributes", {}),
                is_visible=raw.get("is_visible", True),
                is_enabled=raw.get("is_enabled", True),
                is_focusable=raw.get("is_focusable", False),
                has_click_handler=raw.get("has_click_handler", False),
                bounding_box=BoundingBox(**raw["bounding_box"]) if raw.get("bounding_box") else None,
                parent_id=raw.get("parent_id"),
                ancestors=raw.get("ancestors", []),
                matches_recorded_selector=raw.get("matches_recorded_selector", False),
                sibling_index=raw.get("sibling_index", -1),
                sibling_count=raw.get("sibling_count", 0),
                nearby_text=raw.get("nearby_text", ""),
            )
            elements.append(element)
        
        return elements
    
    # Map HTML tags to valid Playwright ARIA roles
    TAG_TO_ROLE = {
        "a": "link",
        "button": "button",
        "input": "textbox",
        "select": "combobox",
        "textarea": "textbox",
        "img": "img",
        "nav": "navigation",
        "form": "form",
        "table": "table",
        "dialog": "dialog",
        "h1": "heading",
        "h2": "heading",
        "h3": "heading",
        "h4": "heading",
        "h5": "heading",
        "h6": "heading",
    }

    async def _get_locator(
        self,
        element: DOMElement,
        action: Optional[ActionNode] = None,
    ) -> Optional[Locator]:
        """
        Get a Playwright locator for a DOMElement.
        """
        # ── Frame routing ───────────────────────────────────────────────────────────
        # Elements extracted from an iframe have __frame_index in their
        # attributes.  All locator lookups use the frame's own locator API
        # instead of self._page so Playwright targets the right execution context.
        _page_root = self._page
        _frame_idx_str = (element.attributes or {}).get("__frame_index")
        if _frame_idx_str is not None:
            try:
                _frame_idx = int(_frame_idx_str)
                _frames = self._page.frames
                if 0 < _frame_idx < len(_frames):
                    candidate_frame = _frames[_frame_idx]
                    # Verify the frame hasn't been replaced since extraction
                    recorded_url = (element.attributes or {}).get("__frame_url", "")
                    if not recorded_url or candidate_frame.url == recorded_url:
                        _page_root = candidate_frame
                        print(f"  [frame] Routing locator through frame[{_frame_idx}] ({candidate_frame.url[:60]})")
                    else:
                        # Index now points to a different frame — search by URL
                        for f in _frames[1:]:
                            if f.url == recorded_url:
                                _page_root = f
                                print(f"  [frame] Stale index corrected; re-found frame by URL ({f.url[:60]})")
                                break
                        else:
                            print(f"  [frame] Warning: original frame gone (was {recorded_url[:60]}); using main frame")
            except (ValueError, TypeError, IndexError):
                pass  # Fall back to main page

        # ── Strategy waterfall ──────────────────────────────────────────────────────────
        #  1. Recorded CSS/XPath selectors (unique preferred)
        #  2. data-testid (unique by definition)
        #  3. ARIA role + name (unique check)
        #  4. Exact text content (unique check)
        #  5. aria-label (unique check)
        #  6. ID attribute (unique by definition)
        #  7. Placeholder (unique check)
        #  8. Name attribute (unique check)
        #  9. Input type (unique check)
        # 10. Role + name with .first (disambiguation fallback)
        # 11. Exact text with .first (disambiguation fallback)
        # 12. Bounding-box elementFromPoint (last resort)
        # 1. Recorded selectors from the action (if available)
        if action and action.target and action.target.selectors:
            try:
                recorded_css = action.target.selectors.css
                if recorded_css:
                    locator = _page_root.locator(recorded_css)
                    css_count = await locator.count()
                    if css_count == 1:
                        return locator
                    if css_count > 1 and element.matches_recorded_selector:
                        return locator.first
            except Exception:
                pass
            try:
                recorded_xpath = action.target.selectors.xpath
                if recorded_xpath:
                    locator = _page_root.locator(f"xpath={recorded_xpath}")
                    xpath_count = await locator.count()
                    if xpath_count == 1:
                        return locator
                    if xpath_count > 1 and element.matches_recorded_selector:
                        return locator.first
            except Exception:
                pass

        # 2. data-testid — unique by definition
        try:
            test_id = (
                element.attributes.get("data-testid") or
                element.attributes.get("data-test-id") or
                element.attributes.get("data-cy")
            )
            if test_id:
                locator = _page_root.get_by_test_id(test_id)
                if await locator.count() == 1:
                    return locator
        except Exception:
            pass
        
        # 3. Role + name — require uniqueness
        try:
            role = element.role
            if role:
                aria_role = self.TAG_TO_ROLE.get(role.lower(), role.lower())
                name = element.aria_label or element.text
                if name:
                    match_name = name.strip().split("\n")[0].strip()[:60]
                    if match_name:
                        locator = _page_root.get_by_role(aria_role, name=match_name)
                        if await locator.count() == 1:
                            return locator
        except Exception:
            pass
        
        # 4. Exact text — require uniqueness
        try:
            if element.text:
                text = element.text.strip()
                if text and len(text) < 100:
                    locator = _page_root.get_by_text(text, exact=True)
                    if await locator.count() == 1:
                        return locator
        except Exception:
            pass
        
        # 5. aria-label — require uniqueness
        try:
            if element.aria_label:
                locator = _page_root.get_by_label(element.aria_label)
                if await locator.count() == 1:
                    return locator
        except Exception:
            pass
        
        # 6. ID attribute — unique by spec
        try:
            if element.attributes.get("id"):
                eid = element.attributes['id'].replace("'", "\\'")
                locator = _page_root.locator(f"[id='{eid}']")
                if await locator.count() == 1:
                    return locator
        except Exception:
            pass
        
        # 7. Placeholder — require uniqueness
        try:
            if element.attributes.get("placeholder"):
                locator = _page_root.get_by_placeholder(element.attributes['placeholder'])
                if await locator.count() == 1:
                    return locator
        except Exception:
            pass
        
        # 8. Name attribute — require uniqueness
        try:
            if element.attributes.get("name"):
                ename = element.attributes['name'].replace("'", "\\'")
                locator = _page_root.locator(f"[name='{ename}']")
                if await locator.count() == 1:
                    return locator
        except Exception:
            pass
                
        # 9. Input type — require uniqueness
        try:
            if element.tag.lower() == "input" and element.attributes.get("type"):
                etype = element.attributes['type'].replace("'", "\\'")
                locator = _page_root.locator(f"input[type='{etype}']")
                if await locator.count() == 1:
                    return locator
        except Exception:
            pass
        
        # 10. Disambiguation fallback: role + name with .first
        try:
            role = element.role
            if role:
                aria_role = self.TAG_TO_ROLE.get(role.lower(), role.lower())
                name = element.aria_label or element.text
                if name:
                    match_name = name.strip().split("\n")[0].strip()[:60]
                    if match_name:
                        locator = _page_root.get_by_role(aria_role, name=match_name)
                        if await locator.count() >= 1:
                            return locator.first
        except Exception:
            pass
        
        # 11. Disambiguation fallback: exact text with .first
        try:
            if element.text:
                text = element.text.strip()
                if text and len(text) < 100:
                    locator = _page_root.get_by_text(text, exact=True)
                    if await locator.count() >= 1:
                        return locator.first
        except Exception:
            pass
        
        # 12. Last resort: bounding-box elementFromPoint
        if element.bounding_box:
            bb = element.bounding_box
            center_x = bb.x + bb.width / 2
            center_y = bb.y + bb.height / 2
            if center_x > 0 and center_y > 0:
                try:
                    tag = element.tag.lower()
                    first_text = (element.text or "").strip().split("\n")[0].strip()[:40]
                    if first_text:
                        escaped_text = first_text.replace("\\", "\\\\").replace("'", "\\'")
                        locator = _page_root.locator(f"{tag}:has-text('{escaped_text}')")
                        try:
                            if await locator.count() >= 1:
                                return locator.first
                        except Exception:
                            pass
                except Exception:
                    pass
        
        return None
