"""
State-Aware Recorder Controller for Axiome Recording Engine.

Extended recorder that captures state intelligence layers
in addition to basic interaction recording.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .core import (
    InteractionObserver,
    InteractionEvent,
    RawBrowserEvent,
    StepAssembler,
    FlowBuilder,
    JsonSerializer,
)
from ..models import (
    Flow,
    ActionType,
    ExtendedStep,
    RecorderConfig,
    DEFAULT_CONFIG,
)
from .state import StateSnapshotBuilder, SemanticPageClassifier, StateDiffEngine
from .graph import InteractionGraphBuilder
from .dom import DOMSnapshotBuilder, DOMDiffEngine
from .transition import StateTransitionBuilder


class StateAwareRecorder:
    """
    State-aware recorder with full intelligence layer capture.
    
    Extends basic recording with:
    - Page state snapshots (before/after interactions)
    - Interaction graphs
    - State transition logs
    - DOM snapshots and diffs
    - Semantic page labels
    
    Recording Pipeline:
    1. User interaction detected
    2. Capture before-state snapshot
    3. Capture before-DOM snapshot (if enabled)
    4. Execute interaction
    5. Wait for page stability
    6. Capture after-state snapshot
    7. Capture after-DOM snapshot
    8. Generate DOM diff
    9. Build interaction graph
    10. Generate state transition log
    11. Apply semantic page labels
    12. Attach all data to extended step
    
    Example:
        async with StateAwareRecorder() as recorder:
            await recorder.start(
                url="https://example.com",
                flow_name="Login Flow",
                project_id="project-1"
            )
            await recorder.wait_for_enter()
            flow = await recorder.stop()
            await recorder.save("output.json")
    """
    
    def __init__(
        self,
        config: Optional[RecorderConfig] = None,
        headless: bool = False,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        slow_mo: int = 0
    ):
        """
        Initialize the state-aware recorder.
        
        Args:
            config: Recorder configuration options
            headless: Run browser in headless mode
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            slow_mo: Slow down operations by ms (for debugging)
        """
        self._config = config or DEFAULT_CONFIG
        self._headless = headless
        self._viewport_width = viewport_width
        self._viewport_height = viewport_height
        self._slow_mo = slow_mo
        
        # Playwright resources
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # Core components
        self._observer = InteractionObserver()
        self._assembler = StepAssembler()
        self._flow_builder = FlowBuilder()
        self._serializer = JsonSerializer()
        
        # State-aware components
        self._state_builder = StateSnapshotBuilder()
        self._classifier = SemanticPageClassifier()
        self._state_diff = StateDiffEngine()
        self._graph_builder = InteractionGraphBuilder()
        self._dom_builder = DOMSnapshotBuilder(self._config)
        self._dom_diff = DOMDiffEngine()
        self._transition_builder = StateTransitionBuilder()
        
        # Recording state
        self._recording = False
        self._last_url: Optional[str] = None
        self._stop_event = asyncio.Event()
        self._active_context_id: Optional[str] = None
        
        # Pre-captured state (for before snapshots)
        self._pending_before_state_by_context: dict[str, Any] = {}
        self._pending_before_dom_by_context: dict[str, Any] = {}
        
        # Sequential processing queue to guarantee step ordering
        self._event_queue: asyncio.Queue[Optional[InteractionEvent]] = asyncio.Queue()
        self._queue_task: Optional[asyncio.Task] = None
        self._listeners = []
        self._active_page_listeners = []
        self._last_step_url: str | None = None
    
    async def __aenter__(self) -> "StateAwareRecorder":
        """Async context manager entry."""
        await self._initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self._cleanup()
    
    async def _initialize(self) -> None:
        """Initialize Playwright browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            slow_mo=self._slow_mo
        )
        self._context = await self._browser.new_context(
            viewport={
                "width": self._viewport_width,
                "height": self._viewport_height
            }
        )
        self._page = await self._context.new_page()
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self._recording:
                await self._observer.detach()
        except Exception:
            pass
        
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
    
    async def start(
        self,
        url: str,
        flow_name: str,
        project_id: str,
        environment: Optional[str] = None
    ) -> None:
        """
        Start a state-aware recording session.
        
        Args:
            url: Starting URL
            flow_name: Human-readable flow name
            project_id: Parent project identifier
            environment: Optional environment name
        """
        if self._recording:
            raise RuntimeError("Recording already in progress")
        
        if not self._page:
            await self._initialize()
        
        # Create new flow
        self._flow_builder.create_flow(
            flow_name=flow_name,
            project_id=project_id,
            base_url=url,
            environment=environment
        )
        
        # Navigate to starting URL
        await self._page.goto(url, wait_until="domcontentloaded")
        self._last_url = url
        # Seed prev_url tracker so the first step can detect URL changes
        self._last_step_url = url
        
        # Attach interaction observer
        await self._observer.attach(self._page)
        self._observer.on_interaction(self._handle_interaction)
        self._observer.on_active_page_changed(self._handle_active_page_changed)
        page_meta = self._observer.get_page_context_metadata(self._page)
        self._active_context_id = page_meta.get("context_id")

        # Capture initial state for the starting context.
        if self._active_context_id:
            await self._capture_pending_state_for_context(self._active_context_id, self._page)
        
        self._recording = True
        self._stop_event.clear()
        
        # Start sequential event processor
        self._queue_task = asyncio.create_task(self._process_queue())
        
        print(f"🎬 State-Aware Recording started: {flow_name}")
        print(f"📍 URL: {url}")
        print(f"⚙️  Config: state={self._config.enable_state_tracking}, "
              f"dom={self._config.enable_dom_snapshots}, "
              f"graph={self._config.enable_interaction_graph}")
        print("🖱️  Interact with the page. Press Enter to stop recording.")
    
    async def stop(self) -> Optional[Flow]:
        """
        Stop the recording session.
        
        Returns:
            The completed Flow object
        """
        if not self._recording:
            return self._flow_builder.get_flow()
        
        self._observer.remove_active_page_callback(self._handle_active_page_changed)
        await self._observer.detach()
        self._stop_event.set()
        
        # Drain the event queue before returning
        if self._queue_task:
            await self._event_queue.put(None)  # Sentinel to stop processor
            try:
                await asyncio.wait_for(self._queue_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._queue_task.cancel()
            self._queue_task = None

        self._recording = False
        
        flow = self._flow_builder.get_flow()
        if flow:
            print(f"\n✅ Recording stopped. Captured {len(flow.steps)} steps.")
        
        return flow
    
    async def save(self, path: Union[str, Path]) -> None:
        """
        Save the recorded flow to a JSON file.
        
        Args:
            path: Output file path
        """
        flow = self._flow_builder.get_flow()
        if not flow:
            raise RuntimeError("No flow to save. Start recording first.")
        
        self._serializer.save_to_file(flow, path)
        print(f"💾 Flow saved to: {path}")
    
    async def wait_for_enter(self) -> None:
        """Wait for user to press Enter to stop recording."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "\nPress Enter to stop recording...")
    
    async def wait_for_user(self, timeout: Optional[float] = None) -> None:
        """Wait for user to finish interacting."""
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            pass
    
    def get_flow(self) -> Optional[Flow]:
        """Get the current flow without stopping."""
        return self._flow_builder.get_flow()
    
    def get_page(self) -> Optional[Page]:
        """Get the Playwright page instance."""
        return self._page

    def on_active_page_changed(self, callback) -> None:
        """Register a callback for recorder active-page changes."""
        self._active_page_listeners.append(callback)

    def remove_active_page_callback(self, callback) -> None:
        """Remove a previously registered recorder active-page callback."""
        if callback in self._active_page_listeners:
            self._active_page_listeners.remove(callback)

    def get_raw_events(self) -> list:
        """Get the raw (lossless) event log from the observer."""
        return self._observer.get_raw_events()
    
    @property
    def is_recording(self) -> bool:
        """Check if recording is in progress."""
        return self._recording
    
    @property
    def step_count(self) -> int:
        """Get the current step count."""
        return self._flow_builder.step_count
    
    async def _capture_pending_state_for_context(self, context_id: str, page: Optional[Page]) -> None:
        """Capture before-state snapshots keyed by browser context id."""
        if not context_id or not page:
            return
        try:
            if self._config.enable_state_tracking:
                self._pending_before_state_by_context[context_id] = await self._state_builder.build(page)

            if self._config.enable_dom_snapshots:
                self._pending_before_dom_by_context[context_id] = await self._dom_builder.build(page)
        except Exception:
            # Navigation may have destroyed context — reset to avoid stale data.
            self._pending_before_state_by_context[context_id] = None
            self._pending_before_dom_by_context[context_id] = None

    async def _capture_pending_state(self) -> None:
        """Backward-compatible wrapper for active context snapshot capture."""
        if self._active_context_id and self._page:
            await self._capture_pending_state_for_context(self._active_context_id, self._page)

    async def _wait_for_stable_context(self, page: Optional[Page]) -> None:
        """Wait for the page execution context to be usable.
        
        After a navigation the old context is destroyed.  We wait for
        domcontentloaded so that subsequent page.title() / page.evaluate()
        calls succeed.
        """
        if not page:
            return
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            # Best-effort; if it times out we proceed anyway
            pass
    
    def _handle_interaction(self, event: InteractionEvent) -> None:
        """Handle captured interaction events with smart deduplication.
        
        Dedup rules:
        1. Submit events are intrinsic to click/Enter — always drop.
        2. Navigate events are intrinsic to interactions — always drop.
           (The observer no longer emits them, but guard here too.)
        """
        if not self._recording:
            return
        
        # --- Rule 1: Drop submit events (intrinsic to click/Enter) ---
        if event.event_type == "submit":
            return
        
        # --- Rule 2: Drop ALL navigate events (always intrinsic) ---
        if event.event_type == "navigate":
            return

        # --- Rule 3: Hover tracking is temporarily disabled ---
        if event.event_type == "hover":
            return

        if event.context_id and event.context_id != self._active_context_id:
            switch_event = InteractionEvent(
                event_type="switch_context",
                timestamp=event.timestamp,
                element_data=None,
                input_value=event.context_id,
                url=event.url,
                context_id=event.context_id,
                opener_context_id=event.opener_context_id,
                page_ref=event.page_ref,
            )
            self._event_queue.put_nowait(switch_event)
            self._active_context_id = event.context_id
            page_for_context = self._observer.get_page_by_context_id(event.context_id)
            if page_for_context:
                self._page = page_for_context
        elif event.context_id and self._active_context_id is None:
            self._active_context_id = event.context_id
        
        # Enqueue for sequential processing (guarantees ordering)
        self._event_queue.put_nowait(event)

    def _handle_active_page_changed(
        self,
        page: Optional[Page],
        metadata: dict[str, Optional[str]],
    ) -> None:
        """Keep recorder page state aligned with observer active page."""
        self._page = page
        self._active_context_id = metadata.get("context_id")
        for listener in list(self._active_page_listeners):
            try:
                listener(page, metadata)
            except Exception:
                pass
    
    async def _process_queue(self) -> None:
        """Sequentially process events from the queue to guarantee ordering."""
        while True:
            event = await self._event_queue.get()
            if event is None:  # Sentinel — stop processing
                break
            await self._process_interaction(event)
    
    async def _process_interaction(self, event: InteractionEvent) -> None:
        """Process an interaction and capture all intelligence layers."""
        if not self._recording:
            return

        context_id = event.context_id or self._active_context_id
        page_for_event = self._observer.get_page_by_context_id(context_id) if context_id else None
        if page_for_event is not None:
            self._page = page_for_event
        page = self._page
        if not page:
            return

        if context_id:
            self._active_context_id = context_id

        try:
            # Get before-state (captured previously)
            before_state = self._pending_before_state_by_context.get(context_id) if context_id else None
            before_dom = self._pending_before_dom_by_context.get(context_id) if context_id else None
            
            # Wait for page stability
            await asyncio.sleep(self._config.stability_wait_ms / 1000)
            
            # If a navigation is in progress (execution context destroyed),
            # wait for the new page to settle before any page queries.
            await self._wait_for_stable_context(page)
            
            # Capture after-state (optional — navigation may still race)
            after_state = None
            if self._config.enable_state_tracking:
                try:
                    after_state = await self._state_builder.build(page)
                except Exception:
                    pass  # Navigation in flight; after-state unavailable
            
            # Capture after-DOM (optional)
            after_dom = None
            if self._config.enable_dom_snapshots:
                try:
                    after_dom = await self._dom_builder.build(page)
                except Exception:
                    pass
            
            # Build base step — this is critical and must not be lost
            step = await self._assembler.assemble(
                event,
                page,
                self._flow_builder.step_count + 1
            )
            
            # Create extended step with intelligence data
            extended_step = ExtendedStep(
                **step.model_dump(),
                before_state_snapshot=before_state if self._config.enable_state_tracking else None,
                after_state_snapshot=after_state if self._config.enable_state_tracking else None,
            )
            
            # Build interaction graph
            if self._config.enable_interaction_graph and after_state:
                extended_step.interaction_graph = await self._graph_builder.build(
                    page, after_state
                )
            
            # Build state transition
            if before_state and after_state:
                # Compute DOM diff
                dom_diff = None
                if before_dom and after_dom:
                    dom_diff = self._dom_diff.compute_diff(before_dom, after_dom)
                    if self._config.include_dom_in_step:
                        extended_step.dom_snapshot_before = before_dom
                        extended_step.dom_snapshot_after = after_dom
                    extended_step.dom_diff = dom_diff
                
                # Build transition
                extended_step.transition_log = self._transition_builder.build(
                    trigger_step_id=step.step_id,
                    before_state=before_state,
                    after_state=after_state,
                    dom_diff=dom_diff
                )
            
            # Apply semantic labels
            if self._config.enable_semantic_labels and after_state:
                extended_step.semantic_page_labels = self._classifier.classify(after_state)
            
            # Compute step hints (auto-inference)
            try:
                from .core.step_hints import compute_step_hints
                step_dict = extended_step.model_dump()
                prev_url = self._last_step_url
                current_url = (step_dict.get("recorded_context") or {}).get("url")

                # Populate state_markers with URL diff so hint engine can use it
                from ..models.context import StepStateMarkers
                state_markers = StepStateMarkers(
                    pre_url=prev_url,
                    post_url=current_url,
                    transition_hint="url_changed" if (prev_url and current_url and prev_url != current_url) else "stable",
                )
                extended_step.state_markers = state_markers
                # Re-dump with markers set
                step_dict = extended_step.model_dump()

                hints = compute_step_hints(
                    step_data=step_dict,
                    step_index=self._flow_builder.step_count,  # 0-based before add
                    total_steps=self._flow_builder.step_count + 1,
                    prev_url=prev_url,
                )
                extended_step.step_hints = hints
                # Track URL for next step's prev_url
                self._last_step_url = current_url
            except Exception as he:
                print(f"  ⚠️ step_hints computation failed: {he}")
            
            # Add to flow
            self._flow_builder.add_step(extended_step)
            
            # Capture next pending state
            if context_id:
                await self._capture_pending_state_for_context(context_id, page)
            
            # Log step capture
            self._log_step(extended_step)
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(extended_step)
                    else:
                        listener(extended_step)
                except Exception as le:
                    print(f"Error in listener: {le}")
            
        except Exception as e:
            print(f"  ⚠️ Error capturing step: {e}")
            import traceback
            traceback.print_exc()
    
    def _log_step(self, step: ExtendedStep) -> None:
        """Log step capture with state info."""
        action_icon = {
            ActionType.CLICK: "🖱️",
            ActionType.HOVER: "👆",
            ActionType.TYPE: "⌨️",
            ActionType.SELECT: "📋",
            ActionType.SUBMIT: "📤",
            ActionType.NAVIGATE: "🔗",
            ActionType.KEYPRESS: "⏎",
            ActionType.SWITCH_CONTEXT: "🗂",
        }.get(step.action, "❓")
        
        target_name = step.target.friendly_name if step.target else step.recorded_context.url
        
        # State info
        state_info = ""
        if step.transition_log and step.transition_log.observed_changes.has_significant_changes:
            changes = step.transition_log.observed_changes
            if changes.url_changed:
                state_info += " [URL↗]"
            if changes.modal_opened:
                state_info += " [Modal↑]"
            if changes.modal_closed:
                state_info += " [Modal↓]"
            if changes.alerts_added:
                state_info += " [Alert!]"
        
        # Labels
        labels_info = ""
        if step.semantic_page_labels and step.semantic_page_labels.labels:
            labels_info = f" [{', '.join(step.semantic_page_labels.labels[:2])}]"
        
        print(f"  {action_icon} Step {step.order}: {step.action.value} → {target_name}{state_info}{labels_info}")

    def add_listener(self, callback):
        """Add a listener for new steps."""
        self._listeners.append(callback)

    def update_step(self, step_id: str, data: dict) -> bool:
        """Update an existing step with new data."""
        flow = self._flow_builder.get_flow()
        if not flow:
            return False

        for step in flow.steps:
            if step.step_id == step_id:
                if "preconditions" in data:
                    from ..models import Precondition
                    raw = data["preconditions"]
                    if isinstance(raw, list):
                        step.preconditions = [
                            Precondition(**p) if isinstance(p, dict) else p
                            for p in raw
                        ]
                    else:
                        step.preconditions = raw

                if "expected_outcome" in data:
                    from ..models import ExpectedOutcome
                    raw = data["expected_outcome"]
                    if isinstance(raw, dict):
                        step.expected_outcome = ExpectedOutcome(**raw)
                    else:
                        step.expected_outcome = raw

                if "test_data" in data:
                    step.test_data = data["test_data"]

                if "failure_behavior" in data:
                    from ..models import FailureBehavior
                    val = data["failure_behavior"]
                    if isinstance(val, str):
                        try:
                            step.failure_behavior = FailureBehavior(val)
                        except ValueError:
                            pass

                if "generalization" in data and step.resolution:
                    from ..models import GeneralizationLevel
                    val = data["generalization"]
                    if isinstance(val, str):
                        try:
                            step.resolution.generalization_level = GeneralizationLevel(val)
                        except ValueError:
                            try:
                                step.resolution.generalization_level = GeneralizationLevel[val.upper()]
                            except KeyError:
                                pass

                return True
        return False

    def delete_step(self, step_id: str) -> bool:
        """Delete a step from the current flow."""
        flow = self._flow_builder.get_flow()
        if not flow:
            return False

        initial_len = len(flow.steps)
        flow.steps = [s for s in flow.steps if s.step_id != step_id]
        return len(flow.steps) < initial_len


async def record_state_aware_session(
    url: str,
    flow_name: str,
    project_id: str,
    output_path: Union[str, Path],
    config: Optional[RecorderConfig] = None,
    environment: Optional[str] = None
) -> Flow:
    """
    Convenience function for state-aware recording sessions.
    
    Args:
        url: Starting URL
        flow_name: Flow name
        project_id: Project ID
        output_path: JSON output path
        config: Optional recorder configuration
        environment: Optional environment name
        
    Returns:
        The recorded Flow
    """
    async with StateAwareRecorder(config=config) as recorder:
        await recorder.start(url, flow_name, project_id, environment)
        await recorder.wait_for_enter()
        flow = await recorder.stop()
        await recorder.save(output_path)
        return flow
