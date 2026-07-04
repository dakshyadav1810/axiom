"""
RecorderManager — multi-user session-isolated recording orchestrator.

Each authenticated user gets their own RecordingSession backed by a
fully isolated Playwright browser instance (separate process, separate
context, separate temp directory).  Concurrent recordings from different
users no longer block each other.
"""

import asyncio
import os
import platform
import tempfile
import shutil
from dataclasses import dataclass, field
from typing import Optional, Union

from axiom_recorder import RecorderController
from axiom_recorder.state_aware_recorder import StateAwareRecorder
from axiom_recorder.models import RecorderConfig, DEFAULT_CONFIG


_SAME_SITE_MAP = {"strict": "Strict", "lax": "Lax", "none": "None"}


@dataclass
class RecordingSession:
    """State for one active recording — fully isolated per user."""
    user_id: str
    recorder: Union[RecorderController, StateAwareRecorder]
    session_state: Optional[dict] = None
    recording_profile: Optional[dict] = None
    temp_dir: Optional[str] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RecorderManager:
    _instance = None

    def __init__(self):
        # user_id → RecordingSession  (one active recording per user)
        self._sessions: dict[str, RecordingSession] = {}
        self._dict_lock = asyncio.Lock()  # guards _sessions mutations only

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RecorderManager()
        return cls._instance

    # ── helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_headless(requested: bool) -> bool:
        """Resolve actual headless flag based on platform/VNC availability."""
        try:
            from .main import vnc_manager as vnc
            if vnc and vnc.running:
                os.environ["DISPLAY"] = vnc.get_display()
                return False
        except Exception:
            pass
        if platform.system() == "Darwin":
            return False
        return requested

    @staticmethod
    async def _inject_session(recorder, session_state: dict) -> None:
        """Inject cookies and storage into a fresh browser context."""
        try:
            cookies = session_state.get("cookies") or []
            if cookies:
                normalised = []
                for c in cookies:
                    c = dict(c)
                    ss = c.get("sameSite")
                    if isinstance(ss, str):
                        c["sameSite"] = _SAME_SITE_MAP.get(ss.lower(), ss)
                    normalised.append(c)
                await recorder._context.add_cookies(normalised)
                print(f"  [auth] Injected {len(normalised)} cookie(s)")
            for entry in (session_state.get("origins") or []):
                origin = (entry.get("origin") or "").rstrip("/")
                ls_data = entry.get("localStorage") or {}
                ss_data = entry.get("sessionStorage") or {}
                if not origin or (not ls_data and not ss_data):
                    continue
                try:
                    await recorder._page.goto(
                        origin, wait_until="domcontentloaded", timeout=10000
                    )
                    if ls_data:
                        await recorder._page.evaluate(
                            "(d)=>{for(const[k,v]of Object.entries(d))"
                            "localStorage.setItem(k,typeof v==='string'?v:JSON.stringify(v))}",
                            ls_data,
                        )
                    if ss_data:
                        await recorder._page.evaluate(
                            "(d)=>{for(const[k,v]of Object.entries(d))"
                            "sessionStorage.setItem(k,typeof v==='string'?v:JSON.stringify(v))}",
                            ss_data,
                        )
                except Exception as se:
                    print(f"  [auth] Storage injection warning for {origin}: {se}")
        except Exception as e:
            print(f"  [auth] Session injection failed: {e}")

    # ── public API ─────────────────────────────────────────────────────────

    async def start_recording(
        self,
        user_id: str,
        url: str,
        flow_name: str,
        project_id: str,
        headless: bool = False,
        state_aware: bool = True,
        config: Optional[RecorderConfig] = None,
        session_state: Optional[dict] = None,
        stream_quality: str = "quality",
        is_mobile: bool = False,
    ):
        # If user already has a session, stop it first (clean up resources)
        existing = self._sessions.get(user_id)
        if existing:
            async with existing.lock:
                try:
                    if existing.recorder.is_recording:
                        await existing.recorder.stop()
                    await existing.recorder._cleanup()
                except Exception:
                    pass
                if existing.temp_dir:
                    shutil.rmtree(existing.temp_dir, ignore_errors=True)
            async with self._dict_lock:
                self._sessions.pop(user_id, None)

        use_headless = self._resolve_headless(headless)
        temp_dir = tempfile.mkdtemp(prefix=f"axiom_{user_id[:8]}_")

        if state_aware:
            recorder = StateAwareRecorder(
                config=config or DEFAULT_CONFIG,
                headless=use_headless,
                viewport_width=390 if is_mobile else 1280,
                viewport_height=844 if is_mobile else 720,
            )
        else:
            recorder = RecorderController(
                headless=use_headless,
                viewport_width=390 if is_mobile else 1280,
                viewport_height=844 if is_mobile else 720,
            )

        setattr(recorder, "_stream_quality", (stream_quality or "quality").strip().lower())
        setattr(recorder, "_is_mobile", bool(is_mobile))

        session = RecordingSession(
            user_id=user_id,
            recorder=recorder,
            session_state=session_state,
            recording_profile={
                "stream_quality": (stream_quality or "quality").strip().lower(),
                "is_mobile": bool(is_mobile),
            },
            temp_dir=temp_dir,
        )

        async with session.lock:
            await recorder._initialize()
            if session_state:
                await self._inject_session(recorder, session_state)
            await recorder.start(url, flow_name, project_id)

        async with self._dict_lock:
            self._sessions[user_id] = session

        print(f"[axiom] Recording started for user={user_id[:8]}… — isolated session in {temp_dir}")
        return recorder

    async def stop_recording(self, user_id: str):
        async with self._dict_lock:
            session = self._sessions.pop(user_id, None)
        if not session:
            return None

        async with session.lock:
            flow = await session.recorder.stop()
            await session.recorder._cleanup()
            if session.temp_dir:
                shutil.rmtree(session.temp_dir, ignore_errors=True)

        print(f"[axiom] Recording stopped for user={user_id[:8]}…")
        return flow

    def get_session_state(self, user_id: str) -> Optional[dict]:
        session = self._sessions.get(user_id)
        return session.session_state if session else None

    def get_recording_profile(self, user_id: str) -> Optional[dict]:
        session = self._sessions.get(user_id)
        return dict(session.recording_profile or {}) if session else None

    def get_active_recording_profile(self) -> Optional[dict]:
        for session in self._sessions.values():
            return dict(session.recording_profile or {})
        return None

    def get_recorder(self, user_id: Optional[str] = None):
        if user_id:
            s = self._sessions.get(user_id)
            return s.recorder if s else None
        # Fallback: first active session (dev/single-user mode)
        for s in self._sessions.values():
            return s.recorder
        return None

    async def update_step(self, step_id: str, data: dict, user_id: Optional[str] = None) -> bool:
        recorder = self.get_recorder(user_id)
        if not recorder:
            return False
        return recorder.update_step(step_id, data)

    async def delete_step(self, step_id: str, user_id: Optional[str] = None) -> bool:
        recorder = self.get_recorder(user_id)
        if not recorder:
            return False
        return recorder.delete_step(step_id)

    # ── legacy shims (keep callers that haven't been updated yet working) ──

    def set_current_user_id(self, user_id: str) -> None:
        pass  # no-op: user_id is now per-session

    def get_current_user_id(self) -> str:
        for s in self._sessions.values():
            return s.user_id
        return "dev-user"
