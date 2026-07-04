"""
Recorder Controller for Axiome Recording Engine.

Main orchestration class that manages the complete recording lifecycle
using Playwright async APIs.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .core import (
    InteractionObserver,
    InteractionEvent,
    RawBrowserEvent,
    StepAssembler,
    FlowBuilder,
    JsonSerializer,
)
from ..models import Flow, ActionType


class RecorderController:
    """
    Main controller for the Axiome Recording Engine.
    
    Orchestrates the complete recording lifecycle:
    1. Launch Playwright browser
    2. Navigate to target URL
    3. Attach interaction listeners
    4. Capture user interactions as Steps
    5. Serialize Flow to JSON
    
    Features:
    - Async Playwright integration
    - Automatic step ordering
    - Graceful shutdown handling
    - Skip duplicate navigate events
    - Interactive mode with console output
    
    Example:
        async with RecorderController() as recorder:
            await recorder.start(
                url="https://example.com",
                flow_name="Example Flow",
                project_id="project-1"
            )
            # Interact with broser...
            await recorder.wait_for_user()
            flow = await recorder.stop()
            await recorder.save("output.json")
    """
    
    def __init__(
        self,
        headless: bool = False,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        slow_mo: int = 0
    ):
        """
        Initialize the recorder controller.
        
        Args:
            headless: Run browser in headless mode
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            slow_mo: Slow down operations by ms (for debugging)
        """
        self._headless = headless
        self._viewport_width = viewport_width
        self._viewport_height = viewport_height
        self._slow_mo = slow_mo
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        self._observer = InteractionObserver()
        self._assembler = StepAssembler()
        self._flow_builder = FlowBuilder()
        self._serializer = JsonSerializer()
        
        self._recording = False
        self._last_url: Optional[str] = None
        self._stop_event = asyncio.Event()
        self._listeners = []
        self._active_page_listeners = []
        self._last_interaction_time: float = 0.0
        self._active_context_id: Optional[str] = None
        
        # Sequential processing queue to guarantee step ordering
        self._event_queue: asyncio.Queue[Optional[InteractionEvent]] = asyncio.Queue()
        self._queue_task: Optional[asyncio.Task] = None
    
    async def __aenter__(self) -> "RecorderController":
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
        Start a recording session.
        
        Navigates to the URL and begins capturing interactions.
        
        Args:
            url: Starting URL to navigate to
            flow_name: Human-readable name for the flow
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
        
        # Attach interaction observer
        await self._observer.attach(self._page)
        self._observer.on_interaction(self._handle_interaction)
        self._observer.on_active_page_changed(self._handle_active_page_changed)
        page_meta = self._observer.get_page_context_metadata(self._page)
        self._active_context_id = page_meta.get("context_id")
        
        self._recording = True
        self._stop_event.clear()
        
        # Start sequential event processor
        self._queue_task = asyncio.create_task(self._process_queue())
        
        print(f"🎬 Recording started: {flow_name}")
        print(f"📍 URL: {url}")
        print("🖱️  Interact with the page. Press Ctrl+C to stop recording.")
    
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
    
    async def wait_for_user(self, timeout: Optional[float] = None) -> None:
        """
        Wait for user to finish interacting.
        
        Waits until stop() is called or timeout expires.
        
        Args:
            timeout: Optional timeout in seconds
        """
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            pass
    
    async def wait_for_enter(self) -> None:
        """
        Wait for user to press Enter to stop recording.
        
        Uses asyncio-compatible input handling.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input, "\nPress Enter to stop recording...")
    
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
        """Process an interaction event and add to flow."""
        if not self._recording:
            return

        context_page = self._observer.get_page_by_context_id(event.context_id)
        if context_page is not None:
            self._page = context_page
        page = self._page
        if not page:
            return

        try:
            step = await self._assembler.assemble(
                event,
                page,
                self._flow_builder.step_count + 1
            )
            
            self._flow_builder.add_step(step)
            
            # Log step capture
            action_icon = {
                ActionType.CLICK: "🖱️",
                ActionType.HOVER: "👆",
                ActionType.TYPE: "⌨️",
                ActionType.SELECT: "📋",
                ActionType.SUBMIT: "📤",
                ActionType.NAVIGATE: "🔗",
                ActionType.WAIT: "⏳",
                ActionType.KEYPRESS: "⏎",
                ActionType.SWITCH_CONTEXT: "🗂",
            }.get(step.action, "❓")
            
            target_name = step.target.friendly_name if step.target else step.recorded_context.url
            print(f"  {action_icon} Step {step.order}: {step.action.value} → {target_name}")
            
            # Notify listeners
            for listener in self._listeners:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(step)
                    else:
                        listener(step)
                except Exception as e:
                    print(f"Error in listener: {e}")
            
        except Exception as e:
            print(f"  ⚠️ Error capturing step: {e}")

    def add_listener(self, callback):
        """Add a listener for new steps."""
        self._listeners.append(callback)

    def update_step(self, step_id: str, data: dict) -> bool:
        """
        Update an existing step with new data.
        
        Args:
            step_id: ID of the step to update
            data: Dictionary of fields to update
            
        Returns:
            True if step was found and updated
        """
        flow = self._flow_builder.get_flow()
        if not flow:
            return False
            
        for step in flow.steps:
            if step.step_id == step_id:
                # Update allowed fields with proper validation
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


async def record_session(
    url: str,
    flow_name: str,
    project_id: str,
    output_path: Union[str, Path],
    environment: Optional[str] = None
) -> Flow:
    """
    Convenience function for simple recording sessions.
    
    Opens a browser, records user interactions, and saves to file.
    
    Args:
        url: Starting URL
        flow_name: Flow name
        project_id: Project ID
        output_path: JSON output path
        environment: Optional environment name
        
    Returns:
        The recorded Flow
    
    Example:
        flow = await record_session(
            url="https://example.com",
            flow_name="My Test",
            project_id="proj-1",
            output_path="test.json"
        )
    """
    async with RecorderController() as recorder:
        await recorder.start(url, flow_name, project_id, environment)
        await recorder.wait_for_enter()
        flow = await recorder.stop()
        await recorder.save(output_path)
        return flow
