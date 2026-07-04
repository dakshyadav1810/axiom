"""
Axiom Server — FastAPI application with all API endpoints.

Endpoints:
  Recording:  POST /api/recording/start, POST /api/recording/stop
  Steps:      PATCH /api/steps/{id}, DELETE /api/steps/{id}
  Projects:   GET/POST /api/projects, GET/PUT/DELETE /api/projects/{id}
  Flows:      GET /api/projects/{id}/flows, GET/PUT/DELETE /api/flows/{id}
  Test:       POST /api/test/run, GET /api/test/runs, GET /api/test/runs/{id}
  Report:     GET /api/test/runs/{id}/report
  WebSocket:  /ws/recording  (step streaming during recording)
              /ws/test/{run_id}  (real-time test progress)
"""

import asyncio
import base64
import json
import os
import platform
import time
import uuid as _uuid
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Literal

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .manager import RecorderManager
from .vnc_manager import VNCManager
from .auth import get_current_user, get_current_user_context, _DEV_MODE, _jwks_client
from ..models import Step
from ..db.repo_factory import (
    get_backend,
    ProjectRepo,
    FlowRepo,
    TestCaseRepo,
    RunGroupRepo,
    TestRunRepo,
    TestResultRepo,
    UsageRepo,
)





# ── Lifespan (DB init / shutdown) ──────────────────────────────────
# Global VNC manager (Linux only; macOS uses CDP fallback)
vnc_manager = VNCManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB backend and VNC stack on startup, close on shutdown."""
    from ..db.repo_factory import _USE_SUPABASE
    if _USE_SUPABASE:
        backend = await get_backend()
        print(f"[axiom] Supabase backend ready")
    else:
        backend = await get_backend()
        print(f"[axiom] SQLite backend ready at {backend.db_path}")

    # Recover any runs stuck in 'running' state from a previous server crash
    try:
        _run_repo_init = TestRunRepo(backend)
        _group_repo_init = RunGroupRepo(backend)
        _stuck_runs = await _run_repo_init.list_by_status("running")
        for _r in _stuck_runs:
            await _run_repo_init.update_status(_r["id"], "failed", failure_class="server_restart")
        if _stuck_runs:
            print(f"[axiom] Recovered {len(_stuck_runs)} stuck test run(s) from previous crash")
        _stuck_groups = await _group_repo_init.list_by_status("running")
        for _g in _stuck_groups:
            await _group_repo_init.update_status(_g["id"], "failed")
        if _stuck_groups:
            print(f"[axiom] Recovered {len(_stuck_groups)} stuck run group(s) from previous crash")
    except Exception as _startup_err:
        print(f"[axiom] Warning: stuck-run recovery failed: {_startup_err}")

    # Start VNC stack on Linux (no-op on macOS)
    if VNCManager.is_available():
        await vnc_manager.start()

    yield

    await vnc_manager.stop()
    # SQLite close (no-op for Supabase)
    if hasattr(backend, 'close'):
        await backend.close()


app = FastAPI(title="Axiom Recorder API", lifespan=lifespan)

# Mount noVNC — resolved relative to the repo so it works both in Docker
# (/app/static/novnc) and local dev (axiom-figma/build/novnc).
_NOVNC_CANDIDATES = [
    Path("/app/static/novnc"),
    Path(__file__).resolve().parent.parent.parent / "axiom-figma" / "build" / "novnc",
]
for _novnc_path in _NOVNC_CANDIDATES:
    if _novnc_path.is_dir():
        app.mount("/novnc", StaticFiles(directory=str(_novnc_path)), name="novnc")
        break

# Artifacts directory — absolute so it resolves correctly regardless of CWD
_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"

# CORS — env-configurable.
# Set ALLOWED_ORIGINS in production, e.g.:
#   ALLOWED_ORIGINS=https://yourdomain.com
# When unset, defaults to "*" so local / early-stage deploys work out of the box.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_cors_origins: list[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins.strip() != "*"
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = RecorderManager.get_instance()

MAX_TEST_WORKERS = max(1, int(os.getenv("AXIOM_MAX_TEST_WORKERS", "4")))
RECORDING_MAX_SECONDS = max(60, int(os.getenv("AXIOM_RECORDING_MAX_SECONDS", "300")))

_recording_timeout_tasks: dict[str, asyncio.Task] = {}
_recording_stop_locks: dict[str, asyncio.Lock] = {}
_usage_locks: dict[str, asyncio.Lock] = {}

# Short-lived (60 s) one-time tokens for /ws/vnc authentication.
# key = UUID token string, value = Unix timestamp of creation.
_vnc_tokens: dict[str, float] = {}


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


async def _get_usage_lock(user_id: str) -> asyncio.Lock:
    lock = _usage_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _usage_locks[user_id] = lock
    return lock


async def _get_recording_stop_lock(user_id: str) -> asyncio.Lock:
    lock = _recording_stop_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _recording_stop_locks[user_id] = lock
    return lock


async def _build_usage_snapshot(backend, user_id: str, user_email: str) -> dict:
    usage_repo = UsageRepo(backend)
    project_repo = ProjectRepo(backend)
    run_group_repo = RunGroupRepo(backend)

    account = await usage_repo.ensure_user_account(user_id, user_email)
    plan = await usage_repo.get_plan(account.get("plan_id", ""))
    if not plan:
        plan = await usage_repo.get_default_plan()
    if not plan:
        raise HTTPException(status_code=500, detail="No usage plan configured")

    max_projects = int(plan.get("max_projects") or 0)
    max_runs_per_project = int(plan.get("max_runs_per_project") or 0)
    is_free_tier = _as_bool(plan.get("is_free_tier", False))
    account_enabled = _as_bool(account.get("account_enabled", True))

    projects = await project_repo.list_all(user_id)
    project_ids = [project.get("id") for project in projects if project.get("id")]
    project_run_counts = await run_group_repo.counts_by_project(project_ids)
    total_runs = sum(project_run_counts.values())

    project_count = len(projects)
    free_tier_hard_lock = is_free_tier and any(
        count >= max_runs_per_project for count in project_run_counts.values()
    )
    usage_blocked = (not account_enabled) or free_tier_hard_lock

    return {
        "account": account,
        "plan": plan,
        "project_count": project_count,
        "project_run_counts": project_run_counts,
        "total_runs": total_runs,
        "max_projects": max_projects,
        "max_runs_per_project": max_runs_per_project,
        "is_free_tier": is_free_tier,
        "account_enabled": account_enabled,
        "usage_blocked": usage_blocked,
        "plan_name": plan.get("name") or "Unknown",
    }


def _assert_account_usable(snapshot: dict) -> None:
    if snapshot.get("usage_blocked"):
        raise HTTPException(
            status_code=402,
            detail=(
                f"Usage limit reached for {snapshot.get('plan_name', 'current')} plan. "
                "Upgrade your account in Supabase (change user_accounts.plan_id) to continue."
            ),
        )


# ── Request / Response Models ──────────────────────────────────────
class StartRecordingRequest(BaseModel):
    url: str
    flow_name: str
    project_id: str
    headless: bool = False
    session_state: Optional[dict] = None  # injected before first navigation
    stream_quality: Literal["quality", "performance"] = "quality"
    is_mobile: bool = False


class UpdateStepRequest(BaseModel):
    data: dict


class CreateProjectRequest(BaseModel):
    name: str
    url: str = ""
    description: str = ""
    validation_goal: str = ""


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    validation_goal: Optional[str] = None
    test_config_json: Optional[dict] = None


class UpdateFlowRequest(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    flow_json: Optional[dict] = None


class RunTestRequest(BaseModel):
    flow_id: Optional[str] = None
    flows: Optional[list[dict]] = None
    headless: bool = True
    timeout: int = 15000
    mode: str = "test_cases"
    test_case_ids: Optional[list[str]] = None
    force_run_variations: bool = False
    diagnostics_policy: Optional[str] = None
    timeout_policy: Optional[str] = None
    session_state: Optional[dict] = None  # {"cookies": [...], "localStorage": {...}, "sessionStorage": {...}}


class GenerateTestCasesRequest(BaseModel):
    flow_id: str
    regenerate: bool = True


class UpdateTestCaseRequest(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


# ── Discovery API Request Models ─────────────────────────────────
class StartDiscoveryRequest(BaseModel):
    project_id: str
    target_url: str
    terminal_goal: str
    max_flows: int = 5
    max_steps: int = 20


class DiscoveryInputResponse(BaseModel):
    request_id: str
    values: dict


# ── WebSocket Connection Manager ──────────────────────────────────
class ConnectionManager:
    """Manages WebSocket connections for recording and test streaming."""

    def __init__(self):
        # Per-user recording connections: user_id → [ws]
        self.recording_connections: Dict[str, List[WebSocket]] = {}
        self.test_connections: Dict[str, List[WebSocket]] = {}  # run_id → [ws]

    async def connect_recording(self, websocket: WebSocket, user_id: str = "dev-user"):
        await websocket.accept()
        self.recording_connections.setdefault(user_id, []).append(websocket)

    def disconnect_recording(self, websocket: WebSocket, user_id: str = "dev-user"):
        conns = self.recording_connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast_recording(self, message: dict, user_id: str = "dev-user"):
        """Broadcast only to the specific user's recording connections."""
        for conn in self.recording_connections.get(user_id, []):
            try:
                await conn.send_json(message)
            except Exception:
                pass

    async def connect_test(self, run_id: str, websocket: WebSocket):
        await websocket.accept()
        self.test_connections.setdefault(run_id, []).append(websocket)

    def disconnect_test(self, run_id: str, websocket: WebSocket):
        conns = self.test_connections.get(run_id, [])
        if websocket in conns:
            conns.remove(websocket)

    async def broadcast_test(self, run_id: str, message: dict):
        for conn in self.test_connections.get(run_id, []):
            try:
                await conn.send_json(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


async def _stop_and_persist_recording(user_id: str, *, reason: str) -> Optional[dict]:
    stop_lock = await _get_recording_stop_lock(user_id)
    async with stop_lock:
        recording_session = manager.get_session_state(user_id)
        recording_profile = manager.get_recording_profile(user_id) or {}
        recorder = manager.get_recorder(user_id)
        recording_artifacts = {}
        if recorder and hasattr(recorder, "get_raw_events"):
            raw_events = recorder.get_raw_events()
            recording_artifacts = {
                "raw_event_count": len(raw_events),
                "curated_step_count": 0,
                "terminated_reason": reason,
            }

        flow = await manager.stop_recording(user_id)
        if not flow:
            return None

        flow_data = json.loads(flow.model_dump_json())
        recording_artifacts["curated_step_count"] = len(flow_data.get("steps", []))

        stream_quality = str(recording_profile.get("stream_quality") or "quality").strip().lower()
        is_mobile = bool(recording_profile.get("is_mobile", False))

        if is_mobile:
            base_name = str(flow_data.get("flow_name") or flow_data.get("name") or "Untitled").strip() or "Untitled"
            if not base_name.endswith(" - Mobile"):
                base_name = f"{base_name} - Mobile"
            flow_data["flow_name"] = base_name
            flow_data["name"] = base_name

        if recording_session:
            gs = flow_data.setdefault("general_settings", {})
            gs["auth_session"] = recording_session

        gs = flow_data.setdefault("general_settings", {})
        gs["stream_quality"] = stream_quality
        gs["is_mobile"] = is_mobile

        try:
            backend = await get_backend()
            flow_repo = FlowRepo(backend)
            await flow_repo.create(
                project_id=flow_data.get("project_id", ""),
                name=flow_data.get("flow_name", flow_data.get("name", "Untitled")),
                base_url=flow_data.get("base_url", ""),
                flow_json=flow_data,
                recording_artifacts_json=recording_artifacts,
                flow_id=flow_data.get("flow_id"),
                is_mobile=is_mobile,
                user_id=user_id,
            )
        except Exception as e:
            print(f"[axiom] Warning: could not save flow to DB: {e}")

        await ws_manager.broadcast_recording(
            {"type": "recording_stopped", "reason": reason},
            user_id=user_id,
        )
        return flow_data


def _cancel_recording_timeout_task(user_id: str) -> None:
    task = _recording_timeout_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()


async def _enforce_recording_timeout(user_id: str) -> None:
    try:
        await asyncio.sleep(RECORDING_MAX_SECONDS)
        await _stop_and_persist_recording(user_id, reason="time_limit")
    except asyncio.CancelledError:
        return
    except Exception as exc:
        print(f"[axiom] Recording timeout enforcement failed for {user_id[:8]}…: {exc}")
    finally:
        _recording_timeout_tasks.pop(user_id, None)


# ══════════════════════════════════════════════════════════════════
# RECORDING ENDPOINTS (existing, unchanged)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/recording/start")
async def start_recording(req: StartRecordingRequest, user_ctx: dict = Depends(get_current_user_context)):
    try:
        user_id = user_ctx["user_id"]
        user_email = user_ctx.get("email") or ""
        backend = await get_backend()
        snapshot = await _build_usage_snapshot(backend, user_id, user_email)
        _assert_account_usable(snapshot)

        _cancel_recording_timeout_task(user_id)
        recorder = await manager.start_recording(
            user_id=user_id,
            url=req.url,
            flow_name=req.flow_name,
            project_id=req.project_id,
            headless=req.headless,
            session_state=req.session_state,
            stream_quality=req.stream_quality,
            is_mobile=req.is_mobile,
        )

        async def on_step(step: Step):
            step_data = json.loads(step.model_dump_json())
            await ws_manager.broadcast_recording(
                {"type": "step_recorded", "payload": step_data},
                user_id=user_id,
            )

        recorder.add_listener(on_step)
        _recording_timeout_tasks[user_id] = asyncio.create_task(_enforce_recording_timeout(user_id))
        return {"status": "started", "url": req.url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/recording/stop")
async def stop_recording(user_id: str = Depends(get_current_user)):
    _cancel_recording_timeout_task(user_id)
    flow_data = await _stop_and_persist_recording(user_id, reason="manual")
    if not flow_data:
        raise HTTPException(status_code=400, detail="No active recording")
    return {"status": "stopped", "flow": flow_data}


@app.patch("/api/steps/{step_id}")
async def update_step(step_id: str, req: UpdateStepRequest, user_id: str = Depends(get_current_user)):
    success = await manager.update_step(step_id, req.data, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Step not found or recorder not active")

    await ws_manager.broadcast_recording(
        {"type": "step_updated", "step_id": step_id, "payload": req.data},
        user_id=user_id,
    )
    return {"status": "updated"}


@app.delete("/api/steps/{step_id}")
async def delete_step(step_id: str, user_id: str = Depends(get_current_user)):
    success = await manager.delete_step(step_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Step not found or recorder not active")

    await ws_manager.broadcast_recording(
        {"type": "step_deleted", "step_id": step_id},
        user_id=user_id,
    )
    return {"status": "deleted"}


# ══════════════════════════════════════════════════════════════════
# PROJECTS API
# ══════════════════════════════════════════════════════════════════

@app.get("/api/projects")
async def list_projects(user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = ProjectRepo(backend)
    projects = await repo.list_all_with_stats(user_id)
    return {"projects": projects}


@app.post("/api/projects")
async def create_project(req: CreateProjectRequest, user_ctx: dict = Depends(get_current_user_context)):
    user_id = user_ctx["user_id"]
    user_email = user_ctx.get("email") or ""
    backend = await get_backend()
    usage_lock = await _get_usage_lock(user_id)
    async with usage_lock:
        snapshot = await _build_usage_snapshot(backend, user_id, user_email)
        _assert_account_usable(snapshot)
        if snapshot["project_count"] >= snapshot["max_projects"]:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Project limit reached ({snapshot['max_projects']}) for {snapshot['plan_name']} plan. "
                    "Upgrade your account in Supabase (change user_accounts.plan_id) to create more projects."
                ),
            )

    repo = ProjectRepo(backend)
    project = await repo.create(
        name=req.name,
        url=req.url,
        description=req.description,
        validation_goal=req.validation_goal,
        user_id=user_id,
    )
    return {"project": project}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = ProjectRepo(backend)
    project = await repo.get(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["stats"] = await repo.get_stats(project_id)
    return {"project": project}


@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, req: UpdateProjectRequest, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = ProjectRepo(backend)
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    project = await repo.update(project_id, user_id, **fields)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project": project}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = ProjectRepo(backend)
    # Verify ownership before cascading
    project = await repo.get(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Cascade: remove child rows so no orphaned data remains
    flow_repo = FlowRepo(backend)
    flows = await flow_repo.list_by_project(project_id, user_id)
    if flows:
        run_repo = TestRunRepo(backend)
        tc_repo = TestCaseRepo(backend)
        group_repo = RunGroupRepo(backend)
        result_repo = TestResultRepo(backend)
        for f in flows:
            fid = f["id"]
            run_ids = await run_repo.list_ids_by_flow(fid)
            if run_ids:
                await result_repo.delete_by_runs(run_ids)
            await run_repo.delete_by_flow(fid)
            await tc_repo.delete_by_flow(fid)
            await group_repo.delete_by_flow(fid)
        for f in flows:
            await flow_repo.delete(f["id"], user_id)
    await repo.delete(project_id, user_id)
    return {"status": "deleted"}


# ══════════════════════════════════════════════════════════════════
# FLOWS API
# ══════════════════════════════════════════════════════════════════

@app.get("/api/projects/{project_id}/flows")
async def list_flows(project_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = FlowRepo(backend)
    flows = await repo.list_by_project(project_id, user_id)
    return {"flows": flows}


@app.get("/api/flows/{flow_id}")
async def get_flow(flow_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = FlowRepo(backend)
    flow = await repo.get(flow_id, user_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return {"flow": flow}


@app.get("/api/flows/{flow_id}/test-cases")
async def list_test_cases(flow_id: str, active_only: bool = Query(False), user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    flow_repo = FlowRepo(backend)
    flow = await flow_repo.get(flow_id, user_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    repo = TestCaseRepo(backend)
    cases = await repo.list_by_flow(flow_id, active_only=active_only)
    return {"test_cases": cases}


@app.put("/api/flows/{flow_id}")
async def update_flow(flow_id: str, req: UpdateFlowRequest, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = FlowRepo(backend)
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    flow = await repo.update(flow_id, user_id, **fields)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return {"flow": flow}


@app.delete("/api/flows/{flow_id}")
async def delete_flow(flow_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = FlowRepo(backend)
    # Verify ownership before cascading.
    flow = await repo.get(flow_id, user_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    # Cascade: remove child rows so no orphaned data accumulates.
    run_repo = TestRunRepo(backend)
    tc_repo = TestCaseRepo(backend)
    group_repo = RunGroupRepo(backend)
    result_repo = TestResultRepo(backend)
    run_ids = await run_repo.list_ids_by_flow(flow_id)
    if run_ids:
        await result_repo.delete_by_runs(run_ids)
    await run_repo.delete_by_flow(flow_id)
    await tc_repo.delete_by_flow(flow_id)
    await group_repo.delete_by_flow(flow_id)
    await repo.delete(flow_id, user_id)
    return {"status": "deleted"}


# ══════════════════════════════════════════════════════════════════
# TEST EXECUTION API
# ══════════════════════════════════════════════════════════════════

@app.post("/api/test-cases/generate")
async def generate_test_cases(req: GenerateTestCasesRequest, user_id: str = Depends(get_current_user)):
    from ..test_engine import generate_and_persist_test_cases

    backend = await get_backend()
    flow_repo = FlowRepo(backend)
    flow = await flow_repo.get(req.flow_id, user_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    cases = await generate_and_persist_test_cases(req.flow_id, regenerate=req.regenerate)
    return {"flow_id": req.flow_id, "test_cases": cases}


@app.patch("/api/test-cases/{test_case_id}")
async def update_test_case(test_case_id: str, req: UpdateTestCaseRequest, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = TestCaseRepo(backend)
    # Verify caller owns the flow this test case belongs to
    test_case = await repo.get(test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    flow = await FlowRepo(backend).get(test_case["flow_id"], user_id)
    if not flow:
        raise HTTPException(status_code=403, detail="Access denied")
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = await repo.update(test_case_id, **fields)
    return {"test_case": updated}


@app.delete("/api/test-cases/{test_case_id}")
async def delete_test_case(test_case_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = TestCaseRepo(backend)
    # Verify caller owns the flow this test case belongs to
    test_case = await repo.get(test_case_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    flow = await FlowRepo(backend).get(test_case["flow_id"], user_id)
    if not flow:
        raise HTTPException(status_code=403, detail="Access denied")
    deleted = await repo.delete(test_case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Test case not found")
    return {"status": "deleted"}


@app.post("/api/test/run")
async def run_test(req: RunTestRequest, user_ctx: dict = Depends(get_current_user_context)):
    """Kick off grouped test-case execution for a flow.
    Keeps `run_id` for backward compatibility as first child run."""
    from ..test_engine import run_test_group

    user_id = user_ctx["user_id"]
    user_email = user_ctx.get("email") or ""
    backend = await get_backend()
    flow_repo = FlowRepo(backend)
    project_repo = ProjectRepo(backend)

    if req.mode == "single":
        raise HTTPException(
            status_code=400,
            detail="Single run mode is disabled. Use test case mode to enforce account usage limits.",
        )

    flow_selections = req.flows or ([{"flow_id": req.flow_id, "test_case_ids": req.test_case_ids}] if req.flow_id else [])
    flow_selections = [sel for sel in flow_selections if sel.get("flow_id")]
    if not flow_selections:
        raise HTTPException(status_code=400, detail="No flows selected")

    owned_flows: list[dict] = []
    project_id: Optional[str] = None
    for selection in flow_selections:
        flow = await flow_repo.get(selection["flow_id"], user_id)
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {selection['flow_id']} not found")
        if project_id is None:
            project_id = flow.get("project_id", "")
        elif flow.get("project_id", "") != project_id:
            raise HTTPException(status_code=400, detail="All selected flows must belong to the same project")
        owned_flows.append(flow)

    primary_flow = owned_flows[0]
    project = await project_repo.get(project_id, user_id) if project_id else None

    usage_lock = await _get_usage_lock(user_id)
    async with usage_lock:
        snapshot = await _build_usage_snapshot(backend, user_id, user_email)
        _assert_account_usable(snapshot)
        current_project_runs = snapshot["project_run_counts"].get(project_id or "", 0)
        if current_project_runs >= snapshot["max_runs_per_project"]:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Run limit reached for this project ({snapshot['max_runs_per_project']} runs) on {snapshot['plan_name']} plan. "
                    "Upgrade your account in Supabase (change user_accounts.plan_id) to run more tests."
                ),
            )

    async def _step_callback(payload: dict):
        msg_type = payload.pop("type", "step_result")
        run_id = payload.get("run_id")
        if run_id:
            await ws_manager.broadcast_test(run_id, {"type": msg_type, **payload})
        await ws_manager.broadcast_test(run_group_id, {"type": msg_type, **payload})

    async def _run_group_in_background(run_group_id: str):
        backend_local = await get_backend()
        group_repo = RunGroupRepo(backend_local)
        try:
            result = await run_test_group(
                flow_selections=flow_selections,
                run_group_id=run_group_id,
                headless=req.headless,
                timeout=req.timeout,
                force_run_variations=req.force_run_variations,
                diagnostics_policy=req.diagnostics_policy,
                timeout_policy=req.timeout_policy,
                on_step=_step_callback,
                session_state=req.session_state,
            )
            runs = result.get("runs", [])
            for child in runs:
                await ws_manager.broadcast_test(child["id"], {"type": "run_complete", **child})
            await ws_manager.broadcast_test(
                run_group_id,
                {"type": "run_group_complete", "run_group": result.get("run_group"), "runs": runs},
            )
        except Exception as e:
            print(f"[axiom] Test run-group {run_group_id} failed: {e}")
            await group_repo.update_status(run_group_id, "failed")

    run_group_repo = RunGroupRepo(backend)
    async with usage_lock:
        latest_snapshot = await _build_usage_snapshot(backend, user_id, user_email)
        _assert_account_usable(latest_snapshot)
        latest_project_runs = latest_snapshot["project_run_counts"].get(project_id or "", 0)
        if latest_project_runs >= latest_snapshot["max_runs_per_project"]:
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Run limit reached for this project ({latest_snapshot['max_runs_per_project']} runs) on {latest_snapshot['plan_name']} plan. "
                    "Upgrade your account in Supabase (change user_accounts.plan_id) to run more tests."
                ),
            )

        run_group = await run_group_repo.create(
            flow_id=primary_flow["id"],
            project_id=primary_flow.get("project_id", ""),
            config={
                "headless": req.headless,
                "timeout": req.timeout,
                "force_run_variations": req.force_run_variations,
                "diagnostics_policy": req.diagnostics_policy,
                "timeout_policy": req.timeout_policy,
                "selected_flows": [
                    {
                        "flow_id": flow["id"],
                        "flow_name": flow.get("name", ""),
                        "test_case_ids": selection.get("test_case_ids") or [],
                    }
                    for flow, selection in zip(owned_flows, flow_selections)
                ],
                "project_name": project.get("name", "") if project else "",
                "project_url": project.get("url", "") if project else "",
                "flow_count": len(flow_selections),
            },
        )
    run_group_id = run_group["id"]
    await run_group_repo.update_status(run_group_id, "running", started_at=_now_iso())
    asyncio.create_task(_run_group_in_background(run_group_id))

    return {"status": "started", "run_id": None, "run_group_id": run_group_id, "run_ids": []}


# ══════════════════════════════════════════════════════════════════
# TEST HISTORY / REPORT API
# ══════════════════════════════════════════════════════════════════

@app.get("/api/test/runs")
async def list_test_runs(
    flow_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user),
):
    """List test runs scoped to the calling user."""
    backend = await get_backend()
    repo = TestRunRepo(backend)
    flow_repo = FlowRepo(backend)
    if flow_id:
        # Verify the caller owns this flow before listing its runs
        flow = await flow_repo.get(flow_id, user_id)
        if not flow:
            raise HTTPException(status_code=403, detail="Access denied")
        runs = await repo.list_by_flow(flow_id, limit=limit)
    else:
        # Scope to runs belonging to the caller via join-based filtering
        runs = await repo.list_by_user(user_id, limit=limit)
    return {"runs": runs}


@app.get("/api/test/runs/{run_id}")
async def get_test_run(run_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    repo = TestRunRepo(backend)
    run = await repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    # Verify caller owns the flow this run belongs to
    flow = await FlowRepo(backend).get(run["flow_id"], user_id)
    if not flow:
        raise HTTPException(status_code=403, detail="Access denied")
    return {"run": run}


def _compute_replay_summary(steps: list[dict]) -> dict:
    """Compute replay-ladder summary from step-level selection_source data."""
    direct_success = 0
    resolver_fallback = 0
    medium_confidence = 0
    total_steps = len(steps)

    for step in steps:
        source = step.get("selection_source") or ""
        if source.startswith("direct"):
            direct_success += 1
        elif source.startswith("resolver"):
            resolver_fallback += 1
        # Check attempt_trace for medium-confidence resolver results
        trace = step.get("attempt_trace_json") or []
        for attempt in trace:
            if isinstance(attempt, dict) and attempt.get("confidence") == "medium":
                medium_confidence += 1
                break

    return {
        "total_steps": total_steps,
        "direct_success_count": direct_success,
        "resolver_fallback_count": resolver_fallback,
        "medium_confidence_count": medium_confidence,
        "deterministic_rate": round(direct_success / total_steps, 3) if total_steps else 0.0,
    }


@app.get("/api/test/runs/{run_id}/report")
async def get_test_report(run_id: str, user_id: str = Depends(get_current_user)):
    """Full test report: run metadata + per-step results."""
    backend = await get_backend()
    run_repo = TestRunRepo(backend)
    result_repo = TestResultRepo(backend)

    run = await run_repo.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    # Verify caller owns the flow this run belongs to
    flow = await FlowRepo(backend).get(run["flow_id"], user_id)
    if not flow:
        raise HTTPException(status_code=403, detail="Access denied")

    steps = await result_repo.list_by_run(run_id)
    diagnostics_json = run.get("diagnostics_json", {}) if isinstance(run, dict) else {}
    diagnostics_summary = diagnostics_json.get("summary", {}) if isinstance(diagnostics_json, dict) else {}
    semantic_assertions = diagnostics_json.get("semantic_assertions", {}) if isinstance(diagnostics_json, dict) else {}
    return {
        "run": run,
        "steps": steps,
        "diagnostics_summary": diagnostics_summary,
        "semantic_assertions": semantic_assertions,
        "verdict": semantic_assertions.get("verdict") if isinstance(semantic_assertions, dict) else None,
        "failure_root_cause": run.get("failure_root_cause"),
        "replay_summary": _compute_replay_summary(steps),
    }


@app.get("/api/test/runs/{run_id}/artifact/{filename}")
async def get_run_artifact(run_id: str, filename: str):
    """Serve a single artifact file (e.g. per-step screenshot) for a test run.

    No auth required — the opaque run UUID acts as an access token, consistent
    with how binary blob endpoints work (S3 pre-signed URLs, etc.).  The path
    traversal guard below ensures no file outside the run's directory is served.
    """
    import re as _re
    # Reject any path traversal attempt
    if _re.search(r'[/\\]|\.\.', filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
    fpath = _ARTIFACTS_DIR / "test_runs" / safe_id / filename
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(str(fpath), headers={"Cache-Control": "private, max-age=86400, immutable"})


@app.get("/api/test/run-groups/{run_group_id}/report")
async def get_run_group_report(run_group_id: str, user_id: str = Depends(get_current_user)):
    backend = await get_backend()
    project_repo = ProjectRepo(backend)
    run_group_repo = RunGroupRepo(backend)
    run_repo = TestRunRepo(backend)
    result_repo = TestResultRepo(backend)
    flow_repo = FlowRepo(backend)

    run_group = await run_group_repo.get(run_group_id)
    if not run_group:
        raise HTTPException(status_code=404, detail="Run group not found")
    project = await project_repo.get(run_group.get("project_id", ""), user_id)
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")

    selected_flows = (run_group.get("config_json") or {}).get("selected_flows") or []
    flow_by_id: dict[str, dict] = {}
    flow_ids = list({item.get("flow_id") for item in selected_flows if item.get("flow_id")})
    if run_group.get("flow_id") and run_group["flow_id"] not in flow_ids:
        flow_ids.append(run_group["flow_id"])
    if flow_ids:
        flows = await flow_repo.list_by_ids(flow_ids, user_id)
        flow_by_id = {flow["id"]: flow for flow in flows if flow.get("id")}

    runs = await run_repo.list_by_run_group(run_group_id)

    detailed_runs = []
    variation_matrix = []
    failure_buckets: dict[str, int] = {}
    verdict_buckets: dict[str, int] = {"pass": 0, "fail": 0, "inconclusive": 0}
    blocked_runs: list[dict] = []
    inactive_or_skipped_reasons: list[dict] = []
    baseline_run = next((r for r in runs if r.get("is_baseline")), None)
    baseline_status = baseline_run.get("status") if baseline_run else None

    # Aggregate replay summary across all runs
    agg_direct = 0
    agg_resolver = 0
    agg_medium = 0
    agg_total = 0

    run_ids = [run["id"] for run in runs if run.get("id")]
    steps_by_run = await result_repo.list_by_runs(run_ids)

    for run in runs:
        steps = steps_by_run.get(run["id"], [])
        if run.get("is_baseline"):
            failure_origin = "baseline"
        elif run.get("status") == "blocked":
            failure_origin = "blocked_by_baseline"
        else:
            failure_origin = "variation_induced" if baseline_status == "passed" else "baseline_degraded"
        run["failure_origin"] = failure_origin
        run_replay = _compute_replay_summary(steps)
        detailed_runs.append({"run": run, "steps": steps, "replay_summary": run_replay})

        # Accumulate for aggregate
        agg_direct += run_replay["direct_success_count"]
        agg_resolver += run_replay["resolver_fallback_count"]
        agg_medium += run_replay["medium_confidence_count"]
        agg_total += run_replay["total_steps"]

        semantic_verdict = (run.get("diagnostics_json") or {}).get("semantic_assertions", {}).get("verdict")
        if semantic_verdict in {"pass", "fail", "inconclusive"}:
            verdict_buckets[semantic_verdict] = verdict_buckets.get(semantic_verdict, 0) + 1

        variation_matrix.append(
            {
                "run_id": run["id"],
                "test_case_id": run.get("test_case_id"),
                "variation_type": run.get("variation_type"),
                "environment_profile": run.get("environment_profile"),
                "status": run.get("status"),
                "verdict": semantic_verdict,
                "is_baseline": run.get("is_baseline"),
                "failure_class": run.get("failure_class"),
                "failure_root_cause": run.get("failure_root_cause"),
                "blocked_reason": run.get("blocked_reason"),
                "failure_origin": failure_origin,
            }
        )
        if run.get("status") == "blocked":
            blocked_runs.append(
                {
                    "run_id": run["id"],
                    "test_case_id": run.get("test_case_id"),
                    "variation_type": run.get("variation_type"),
                    "blocked_reason": run.get("blocked_reason"),
                }
            )
        # Track skipped / inactive runs
        if run.get("status") == "skipped" or not run.get("active", True):
            inactive_or_skipped_reasons.append(
                {
                    "run_id": run["id"],
                    "test_case_id": run.get("test_case_id"),
                    "variation_type": run.get("variation_type"),
                    "status": run.get("status"),
                    "reason": run.get("blocked_reason") or run.get("skip_reason") or "inactive",
                }
            )
        bucket = run.get("failure_class") or ("blocked" if run.get("status") == "blocked" else None)
        if bucket:
            failure_buckets[bucket] = failure_buckets.get(bucket, 0) + 1

    # Compatibility flags for the group
    variation_mode = run_group.get("variation_mode") or "full"
    compatibility_flags = {
        "variation_mode": variation_mode,
        "compat_only": variation_mode == "compat_only",
        "replay_mode": run_group.get("replay_mode") or "deterministic_first",
        "resolver_fallback_policy": run_group.get("resolver_fallback_policy") or "balanced",
    }

    aggregate_replay_summary = {
        "total_steps": agg_total,
        "direct_success_count": agg_direct,
        "resolver_fallback_count": agg_resolver,
        "medium_confidence_count": agg_medium,
        "deterministic_rate": round(agg_direct / agg_total, 3) if agg_total else 0.0,
    }

    return {
        "run_group": run_group,
        "project": {
            "id": project.get("id", ""),
            "name": project.get("name", ""),
            "url": project.get("url", ""),
        },
        "flow": {
            "id": run_group["flow_id"],
            "name": flow_by_id.get(run_group["flow_id"], {}).get("name", "") if run_group.get("flow_id") else "",
            "project_id": run_group.get("project_id", ""),
        },
        "flows": [
            {
                "id": flow_id,
                "name": flow_by_id.get(flow_id, {}).get("name") or next((r.get("flow_name") for r in runs if r.get("flow_id") == flow_id), ""),
                "project_id": run_group.get("project_id", ""),
            }
            for flow_id in (flow_ids or list({run.get("flow_id") for run in runs if run.get("flow_id")}))
        ],
        "runs": detailed_runs,
        "variation_matrix": variation_matrix,
        "blocked_runs": blocked_runs,
        "failure_buckets": failure_buckets,
        "verdict_buckets": verdict_buckets,
        "replay_summary": aggregate_replay_summary,
        "compatibility_flags": compatibility_flags,
        "inactive_or_skipped_reasons": inactive_or_skipped_reasons,
    }


# ══════════════════════════════════════════════════════════════════
# WEBSOCKETS
# ══════════════════════════════════════════════════════════════════

@app.websocket("/ws/recording")
async def ws_recording(websocket: WebSocket):
    """Recording WebSocket. Auth via first JSON message to keep JWT out of server logs:
       client → server: {"type": "auth", "token": "<jwt>"}
    """
    await websocket.accept()
    if _DEV_MODE:
        user_id = "dev-user"
    else:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            msg = json.loads(raw)
            if msg.get("type") != "auth" or not msg.get("token"):
                await websocket.close(code=4401)
                return
            token = msg["token"]
            import jwt as _jwt
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = _jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256", "HS256"],
                audience="authenticated",
            )
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=4401)
                return
        except Exception:
            await websocket.close(code=4401)
            return
    ws_manager.recording_connections.setdefault(user_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_recording(websocket, user_id)


@app.websocket("/ws/test/{run_id}")
async def ws_test(run_id: str, websocket: WebSocket):
    """Real-time test progress. Auth via first JSON message: {"type": "auth", "token": "<jwt>"}"""
    await websocket.accept()
    if not _DEV_MODE:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            msg = json.loads(raw)
            if msg.get("type") != "auth" or not msg.get("token"):
                await websocket.close(code=4401)
                return
            token = msg["token"]
            import jwt as _jwt
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = _jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256", "HS256"],
                audience="authenticated",
            )
            if not payload.get("sub"):
                await websocket.close(code=4401)
                return
        except Exception:
            await websocket.close(code=4401)
            return
    ws_manager.test_connections.setdefault(run_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_test(run_id, websocket)


# ══════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# BROWSER STREAM
# ══════════════════════════════════════════════════════════════════

@app.get("/api/browser/stream-info")
async def browser_stream_info():
    """Return connection info for the browser stream viewer.

    On Linux (VNC available):
        { mode: "vnc" }  — frontend connects via /ws/vnc proxy on port 8000
    On macOS (CDP fallback):
        { mode: "cdp" }
    Not recording:
        { mode: "none" }
    """
    recorder = manager.get_recorder()

    if vnc_manager.running:
        # Return mode=vnc but no port — frontend uses /ws/vnc proxy so only
        # port 8000 needs to be open in the EC2 security group.
        return {"mode": "vnc"}
    elif recorder and recorder.is_recording:
        return {"mode": "cdp"}
    else:
        return {"mode": "none"}


@app.get("/api/browser/vnc-token")
async def get_vnc_token(user_id: str = Depends(get_current_user)):
    """Issue a short-lived (60 s) one-time token for authenticating /ws/vnc.

    The browser fetches this before connecting noVNC, then appends
    ?token=<value> to the WebSocket URL.  The token is consumed on first use.
    """
    token = str(_uuid.uuid4())
    _vnc_tokens[token] = time.time()
    return {"token": token}


@app.websocket("/ws/vnc")
async def ws_vnc_proxy(websocket: WebSocket, token: str = Query(default="")):
    """WebSocket proxy: browser  ←→  /ws/vnc (port 8000)  ←→  websockify (port 6080).

    Requires a one-time token obtained from GET /api/browser/vnc-token.
    The raw websockify port 6080 stays localhost-only.
    """
    if not _DEV_MODE:
        now = time.time()
        # Purge expired tokens on each connection attempt.
        for k in [k for k, ts in list(_vnc_tokens.items()) if now - ts > 60]:
            _vnc_tokens.pop(k, None)
        if token not in _vnc_tokens:
            # Must accept before we can send a close code.
            await websocket.accept()
            await websocket.close(code=4401)
            return
        _vnc_tokens.pop(token)  # one-time use
    await websocket.accept(subprotocol="binary")

    import websockets as _ws_lib
    vnc_url = f"ws://localhost:{vnc_manager.ws_port}"
    try:
        async with _ws_lib.connect(vnc_url, subprotocols=["binary"]) as vnc_ws:
            async def browser_to_vnc():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await vnc_ws.send(data)
                except Exception:
                    pass

            async def vnc_to_browser():
                try:
                    async for msg in vnc_ws:
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(msg)
                except Exception:
                    pass

            await asyncio.gather(browser_to_vnc(), vnc_to_browser())
    except Exception as e:
        print(f"[vnc-proxy] Connection failed: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


@app.websocket("/ws/browser-stream")
async def ws_browser_stream(websocket: WebSocket):
    """CDP screencast fallback for macOS development.

    Streams JPEG frames from the Playwright browser via Chrome DevTools
    Protocol.  The frontend renders frames onto a <canvas>.

    Auth via first JSON message: {"type": "auth", "token": "<jwt>"}

    Server → Client messages:
        Binary:  Raw JPEG frame bytes
        JSON:    { type: "meta", width, height, url, title }

    Client → Server messages:
        JSON:    { type: "mousemove|click|mousedown|mouseup|wheel|keydown|keyup|type|resize", ... }
    """
    await websocket.accept()

    # Auth check — same first-message pattern as /ws/recording and /ws/test
    if not _DEV_MODE:
        try:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            msg = json.loads(raw)
            if msg.get("type") != "auth" or not msg.get("token"):
                await websocket.close(code=4401)
                return
            token = msg["token"]
            import jwt as _jwt
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = _jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256", "HS256"],
                audience="authenticated",
            )
            if not payload.get("sub"):
                await websocket.close(code=4401)
                return
        except Exception:
            await websocket.close(code=4401)
            return

    recorder = manager.get_recorder()
    if not recorder or not recorder._page:
        await websocket.send_json({"type": "error", "message": "No active recording"})
        await websocket.close()
        return

    # Track whether we're still connected.
    connected = True
    frame_queue: asyncio.Queue = asyncio.Queue(maxsize=2)  # Drop old frames.
    page_change_queue: asyncio.Queue = asyncio.Queue(maxsize=8)
    stream_lock = asyncio.Lock()
    active_stream: dict[str, object] = {
        "page": None,
        "cdp": None,
        "viewport": {"width": 1280, "height": 720},
        "stream_key": 0,
    }

    active_profile = manager.get_active_recording_profile() or {}
    stream_quality = str(
        active_profile.get("stream_quality")
        or getattr(recorder, "_stream_quality", "quality")
        or "quality"
    ).strip().lower()
    jpeg_quality = 50 if stream_quality == "performance" else 75
    every_nth_frame = 2 if stream_quality == "performance" else 1

    def _get_context_metadata(page_obj) -> dict:
        observer = getattr(recorder, "_observer", None)
        if not observer:
            return {}
        getter = getattr(observer, "get_page_context_metadata", None)
        if not getter:
            return {}
        try:
            data = getter(page_obj)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    async def _send_meta_for_page(page_obj, viewport_obj: dict, *, reason: str = "update") -> None:
        if not page_obj:
            return
        try:
            title = await page_obj.title()
        except Exception:
            title = ""
        meta_payload = {
            "type": "meta",
            "reason": reason,
            "width": int(viewport_obj.get("width") or 1280),
            "height": int(viewport_obj.get("height") or 720),
            "url": page_obj.url,
            "title": title,
        }
        context_meta = _get_context_metadata(page_obj)
        if context_meta:
            meta_payload["context_id"] = context_meta.get("context_id")
            meta_payload["opener_context_id"] = context_meta.get("opener_context_id")
            meta_payload["page_ref"] = context_meta.get("page_ref")
        await websocket.send_json(meta_payload)

    async def _stop_stream_session(session: dict) -> None:
        cdp_session = session.get("cdp")
        if not cdp_session:
            return
        with suppress(Exception):
            await cdp_session.send("Page.stopScreencast")
        with suppress(Exception):
            await cdp_session.detach()

    async def _rebind_to_page(target_page) -> bool:
        """Switch screencast/input CDP session to the recorder's active page."""
        nonlocal active_stream
        if not target_page:
            return False
        if target_page.is_closed():
            return False

        old_session: dict = {}
        created_session: dict = {}
        try:
            async with stream_lock:
                current_page = active_stream.get("page")
                current_cdp = active_stream.get("cdp")
                if current_page is target_page and current_cdp:
                    return True

                try:
                    cdp_session = await target_page.context.new_cdp_session(target_page)
                except Exception as session_err:
                    print(f"[stream] CDP session failed during rebind: {session_err}")
                    return False

                viewport = target_page.viewport_size or {"width": 1280, "height": 720}
                stream_key = int(active_stream.get("stream_key") or 0) + 1
                old_session = dict(active_stream)
                active_stream = {
                    "page": target_page,
                    "cdp": cdp_session,
                    "viewport": viewport,
                    "stream_key": stream_key,
                }
                created_session = dict(active_stream)

                def on_frame(params: dict, *, _stream_key: int = stream_key, _cdp=cdp_session, _page=target_page, _viewport=viewport):
                    if not connected:
                        return
                    if int(active_stream.get("stream_key") or 0) != _stream_key:
                        return
                    payload = {
                        "params": params,
                        "cdp": _cdp,
                        "page": _page,
                        "viewport": _viewport,
                    }
                    try:
                        frame_queue.put_nowait(payload)
                    except asyncio.QueueFull:
                        try:
                            frame_queue.get_nowait()
                            frame_queue.put_nowait(payload)
                        except Exception:
                            pass

                cdp_session.on("Page.screencastFrame", on_frame)

                await cdp_session.send(
                    "Page.startScreencast",
                    {
                        "format": "jpeg",
                        "quality": jpeg_quality,
                        "maxWidth": int(viewport.get("width") or 1280),
                        "maxHeight": int(viewport.get("height") or 720),
                        "everyNthFrame": every_nth_frame,
                    },
                )

                # Flush stale queued frames from the previous page to avoid
                # mixing contexts right after a rebind.
                while not frame_queue.empty():
                    with suppress(Exception):
                        frame_queue.get_nowait()
        except Exception as rebind_err:
            print(f"[stream] Rebind failed: {rebind_err}")
            await _stop_stream_session(created_session)
            async with stream_lock:
                if (
                    created_session.get("stream_key")
                    and int(active_stream.get("stream_key") or 0) == int(created_session.get("stream_key") or 0)
                ):
                    active_stream = old_session or {
                        "page": None,
                        "cdp": None,
                        "viewport": {"width": 1280, "height": 720},
                        "stream_key": int(active_stream.get("stream_key") or 0),
                    }
            return False

        try:
            await _send_meta_for_page(
                created_session.get("page"),
                created_session.get("viewport") or {"width": 1280, "height": 720},
                reason="rebind",
            )
        except Exception as meta_err:
            print(f"[stream] Meta update failed after rebind: {meta_err}")

        if old_session.get("cdp"):
            await _stop_stream_session(old_session)
        return True

    async def _send_frames():
        """Continuously send frames from the queue."""
        nonlocal connected
        while connected:
            try:
                payload = await asyncio.wait_for(frame_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

            params = payload.get("params") if isinstance(payload, dict) else None
            cdp_session = payload.get("cdp") if isinstance(payload, dict) else None
            frame_page = payload.get("page") if isinstance(payload, dict) else None
            viewport_obj = payload.get("viewport") if isinstance(payload, dict) else None
            if not isinstance(params, dict):
                continue

            try:
                # Ack frame best-effort so CDP keeps sending.
                if cdp_session and params.get("sessionId") is not None:
                    with suppress(Exception):
                        await cdp_session.send(
                            "Page.screencastFrameAck",
                            {"sessionId": params["sessionId"]},
                        )

                frame_bytes = base64.b64decode(params["data"])
                await websocket.send_bytes(frame_bytes)

                meta = params.get("metadata", {})
                if meta:
                    width = int((viewport_obj or {}).get("width") or 1280)
                    height = int((viewport_obj or {}).get("height") or 720)
                    meta_payload = {
                        "type": "meta",
                        "reason": "frame",
                        "url": meta.get("pageUrl") or (frame_page.url if frame_page else ""),
                        "title": meta.get("pageTitle", ""),
                        "width": width,
                        "height": height,
                    }
                    context_meta = _get_context_metadata(frame_page)
                    if context_meta:
                        meta_payload["context_id"] = context_meta.get("context_id")
                        meta_payload["opener_context_id"] = context_meta.get("opener_context_id")
                        meta_payload["page_ref"] = context_meta.get("page_ref")
                    await websocket.send_json(meta_payload)
            except WebSocketDisconnect:
                connected = False
                break
            except Exception as e:
                print(f"[stream] Frame send error: {e}")
                break

    async def _receive_input():
        """Receive and dispatch input events from the client."""
        nonlocal connected
        while connected:
            try:
                raw = await websocket.receive_text()
                event = json.loads(raw)
                etype = event.get("type")

                async with stream_lock:
                    cdp_session = active_stream.get("cdp")
                    if not cdp_session:
                        continue

                    if etype in ("mousemove", "mousedown", "mouseup", "click"):
                        cdp_type_map = {
                            "mousemove": "mouseMoved",
                            "mousedown": "mousePressed",
                            "mouseup": "mouseReleased",
                            "click": "mousePressed",  # Press + release.
                        }
                        params = {
                            "type": cdp_type_map[etype],
                            "x": event.get("x", 0),
                            "y": event.get("y", 0),
                            "button": event.get("button", "left"),
                            "clickCount": 1 if etype in ("click", "mousedown") else 0,
                        }
                        await cdp_session.send("Input.dispatchMouseEvent", params)
                        if etype == "click":
                            params["type"] = "mouseReleased"
                            await cdp_session.send("Input.dispatchMouseEvent", params)

                    elif etype == "wheel":
                        await cdp_session.send(
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mouseWheel",
                                "x": event.get("x", 0),
                                "y": event.get("y", 0),
                                "deltaX": event.get("deltaX", 0),
                                "deltaY": event.get("deltaY", 0),
                            },
                        )

                    elif etype == "keydown":
                        await cdp_session.send(
                            "Input.dispatchKeyEvent",
                            {
                                "type": "keyDown",
                                "key": event.get("key", ""),
                                "code": event.get("code", ""),
                                "text": event.get("key", "") if len(event.get("key", "")) == 1 else "",
                                "windowsVirtualKeyCode": event.get("keyCode", 0),
                            },
                        )

                    elif etype == "keyup":
                        await cdp_session.send(
                            "Input.dispatchKeyEvent",
                            {
                                "type": "keyUp",
                                "key": event.get("key", ""),
                                "code": event.get("code", ""),
                            },
                        )

                    elif etype == "type":
                        for char in event.get("text", ""):
                            await cdp_session.send(
                                "Input.dispatchKeyEvent",
                                {
                                    "type": "char",
                                    "text": char,
                                },
                            )

            except WebSocketDisconnect:
                connected = False
                break
            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"[stream] Input error: {e}")
                continue

    def _enqueue_active_page_change(page, _metadata) -> None:
        """Receive recorder active-page changes without polling recorder state."""
        if not connected or not page or page.is_closed():
            return
        try:
            page_change_queue.put_nowait(page)
        except asyncio.QueueFull:
            try:
                page_change_queue.get_nowait()
                page_change_queue.put_nowait(page)
            except Exception:
                pass

    async def _follow_active_page():
        """Auto-follow recorder active-page changes from the recorder hook."""
        nonlocal connected
        while connected:
            try:
                active_page = await asyncio.wait_for(page_change_queue.get(), timeout=0.5)
                if not active_page or active_page.is_closed():
                    continue
                if active_page is not active_stream.get("page"):
                    await _rebind_to_page(active_page)
            except asyncio.TimeoutError:
                continue
            except Exception as follow_err:
                print(f"[stream] Active page follow warning: {follow_err}")

    # Initial bind to the currently active recorder page.
    if not await _rebind_to_page(recorder._page):
        await websocket.send_json({"type": "error", "message": "Failed to start browser stream"})
        await websocket.close()
        return

    if hasattr(recorder, "on_active_page_changed"):
        recorder.on_active_page_changed(_enqueue_active_page_change)
    follow_task = asyncio.create_task(_follow_active_page())

    try:
        await asyncio.gather(_send_frames(), _receive_input())
    except Exception as e:
        print(f"[stream] Error in frame/input loop: {type(e).__name__}: {e}")
    finally:
        connected = False
        if hasattr(recorder, "remove_active_page_callback"):
            recorder.remove_active_page_callback(_enqueue_active_page_change)
        follow_task.cancel()
        with suppress(asyncio.CancelledError):
            await follow_task

        final_session = {}
        async with stream_lock:
            final_session = dict(active_stream)
            active_stream = {
                "page": None,
                "cdp": None,
                "viewport": {"width": 1280, "height": 720},
                "stream_key": int(final_session.get("stream_key") or 0),
            }
        await _stop_stream_session(final_session)


# ══════════════════════════════════════════════════════════════════
# DISCOVERY API (LLM-powered flow generation)
# ══════════════════════════════════════════════════════════════════

# Import discovery components (behind feature flag)
if os.environ.get("AXIOM_ENABLE_DISCOVERY_API") == "1":
    try:
        from ..discovery.job_manager import DiscoveryJobManager, JobStatus
        from ..discovery.explorer import DeepExplorer
        from ..discovery.models import Flow as DiscoveryFlow
        from ..discovery.converter import DiscoveryToAxiomConverter
    except ImportError as e:
        print(f"[discovery] Warning: Could not import discovery modules: {e}")
        # Set to None to avoid NameError
        DiscoveryJobManager = None
        DeepExplorer = None
        DiscoveryFlow = None
        DiscoveryToAxiomConverter = None
    
    @app.post("/api/discovery/run")
    async def start_discovery_job(
        req: StartDiscoveryRequest,
        user_ctx: dict = Depends(get_current_user_context),
    ):
        """Start a new discovery job to auto-generate flows."""
        user_id = user_ctx["user_id"]
        
        # Check usage limits
        backend = await get_backend()
        snapshot = await _build_usage_snapshot(backend, user_id, user_ctx.get("email") or "")
        _assert_account_usable(snapshot)
        
        # Create job
        job_manager = await DiscoveryJobManager.get_instance()
        job = await job_manager.create_job(
            user_id=user_id,
            target_url=req.target_url,
            terminal_goal=req.terminal_goal,
            max_flows=req.max_flows,
            max_steps=req.max_steps,
            llm_budget_usd=1.0,  # $1 limit
        )
        
        # Start background task
        asyncio.create_task(
            _run_discovery_job(job.job_id, req.project_id, user_id)
        )
        
        return {
            "status": "started",
            "job_id": job.job_id,
        }
    
    @app.get("/api/discovery/jobs/{job_id}")
    async def get_discovery_job(
        job_id: str,
        user_ctx: dict = Depends(get_current_user_context),
    ):
        """Get status of a discovery job."""
        user_id = user_ctx["user_id"]
        job_manager = await DiscoveryJobManager.get_instance()
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "created_at": datetime.fromtimestamp(job.created_at).isoformat(),
            "updated_at": datetime.fromtimestamp(job.updated_at).isoformat(),
            "target_url": job.target_url,
            "terminal_goal": job.terminal_goal,
            "max_flows": job.max_flows,
            "created_flow_ids": job.created_flow_ids,
            "captured_auth_session": job.captured_auth_session,
            "last_progress": job.last_progress_payload,
            "error_message": job.error_message,
            "llm_usage": {
                "calls": job.llm_calls_made,
                "tokens": job.tokens_used,
                "estimated_cost_usd": job.estimated_cost_usd,
            },
        }
    
    @app.get("/api/discovery/jobs/{job_id}/flows")
    async def get_discovery_job_flows(
        job_id: str,
        user_ctx: dict = Depends(get_current_user_context),
    ):
        """Get flows created by a discovery job."""
        user_id = user_ctx["user_id"]
        backend = await get_backend()
        flow_repo = FlowRepo(backend)
        
        job_manager = await DiscoveryJobManager.get_instance()
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Fetch all created flows
        flows = []
        for flow_id in job.created_flow_ids:
            flow_data = await flow_repo.get(flow_id)
            if flow_data:
                flows.append({
                    "id": flow_data["id"],
                    "name": flow_data["name"],
                    "step_count": len(flow_data.get("flow_json", {}).get("steps", [])),
                    "created_at": flow_data["created_at"],
                })
        
        return {
            "job_id": job_id,
            "flows": flows,
            "captured_auth_session": job.captured_auth_session,
        }
    
    @app.post("/api/discovery/jobs/{job_id}/cancel")
    async def cancel_discovery_job(
        job_id: str,
        user_ctx: dict = Depends(get_current_user_context),
    ):
        """Cancel a running discovery job."""
        user_id = user_ctx["user_id"]
        job_manager = await DiscoveryJobManager.get_instance()
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await job_manager.cancel_job(job_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be cancelled (already completed or failed)",
            )
        
        return {"status": "cancelled", "job_id": job_id}
    
    @app.post("/api/discovery/jobs/{job_id}/input")
    async def submit_discovery_input(
        job_id: str,
        req: DiscoveryInputResponse,
        user_ctx: dict = Depends(get_current_user_context),
    ):
        """Submit values for an input request from the discovery engine."""
        user_id = user_ctx["user_id"]
        job_manager = await DiscoveryJobManager.get_instance()
        job = await job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        success = await job_manager.submit_input_response(
            job_id=job_id,
            request_id=req.request_id,
            values=req.values,
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid request_id or request already fulfilled",
            )
        
        return {"status": "submitted"}
    
    @app.websocket("/ws/discovery/{job_id}")
    async def discovery_websocket(websocket: WebSocket, job_id: str):
        """WebSocket endpoint for discovery job progress streaming."""
        job_manager = await DiscoveryJobManager.get_instance()
        job = await job_manager.get_job(job_id)
        
        if not job:
            await websocket.close(code=4004, reason="Job not found")
            return
        
        # Accept connection
        await websocket.accept()
        
        # Wait for auth message (first message must be auth)
        try:
            auth_data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=10.0
            )
            
            if not isinstance(auth_data, dict) or auth_data.get("type") != "auth":
                await websocket.close(code=4003, reason="First message must be auth")
                return
            
            # Validate JWT token
            token = auth_data.get("token")
            if not token:
                await websocket.close(code=4001, reason="Missing token")
                return
            
            # Verify token using existing auth logic
            if not _DEV_MODE:
                try:
                    import jwt
                    signing_key = _jwks_client.get_signing_key_from_jwt(token)
                    payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=["ES256", "RS256", "HS256"],
                        audience="authenticated",
                    )
                    token_user_id = payload.get("sub")
                    if not token_user_id or token_user_id != job.user_id:
                        await websocket.close(code=4003, reason="Invalid token")
                        return
                except Exception:
                    await websocket.close(code=4003, reason="Invalid token")
                    return
            
            # Connect to job
            await job_manager.connect_ws(job_id, websocket)
            
            # Send last progress if available
            if job.last_progress_payload:
                await websocket.send_json(job.last_progress_payload)
            
            # Keep connection alive
            try:
                while True:
                    # Handle incoming messages (input_response, ping, etc.)
                    message = await websocket.receive_json()
                    msg_type = message.get("type")
                    
                    if msg_type == "input_response":
                        # Forward to job manager
                        await job_manager.submit_input_response(
                            job_id=job_id,
                            request_id=message.get("request_id"),
                            values=message.get("values", {}),
                        )
                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong"})
                        
            except WebSocketDisconnect:
                pass
            finally:
                job_manager.disconnect_ws(job_id, websocket)
                
        except asyncio.TimeoutError:
            await websocket.close(code=4008, reason="Auth timeout")
        except Exception as e:
            print(f"[discovery] WebSocket error: {e}")
            try:
                await websocket.close(code=4000, reason="Connection error")
            except Exception:
                pass
    
    async def _run_discovery_job(
        job_id: str,
        project_id: str,
        user_id: str,
    ):
        """Background task to run discovery job."""
        job_manager = await DiscoveryJobManager.get_instance()
        job = await job_manager.get_job(job_id)
        
        if not job:
            return
        
        try:
            # Update status to running
            await job_manager.update_job_status(job_id, JobStatus.RUNNING)
            
            # Send initial progress
            await job_manager.send_progress(
                job_id,
                stage="initializing",
                percent=0,
                message="Starting discovery engine...",
            )
            
            # Create input callback for interactive flows
            async def input_callback(step) -> str:
                """Request input from user via WebSocket."""
                # Derive field schema from step
                request_id = f"{job_id}:{_uuid.uuid4()}"
                
                # Build field schema based on step hints or defaults
                fields = []
                if hasattr(step, 'step_hints') and step.step_hints.get('input_schema'):
                    schema = step.step_hints['input_schema']
                    fields.append({
                        "name": schema.get("field_name", "value"),
                        "label": schema.get("label", "Input required"),
                        "input_type": schema.get("input_type", "text"),
                        "required": schema.get("required", True),
                        "value_hint": schema.get("value_hint"),
                    })
                else:
                    # Fallback: generic field
                    fields.append({
                        "name": "value",
                        "label": "Input required for this step",
                        "input_type": "text",
                        "required": True,
                    })
                
                # Request values from client
                values = await job_manager.send_input_request(
                    job_id=job_id,
                    request_id=request_id,
                    fields=fields,
                )
                
                # Return the value
                return values.get("value") or values.get(fields[0]["name"], "")
            
            # Create and run explorer
            explorer = DeepExplorer(
                target_url=job.target_url,
                input_callback=input_callback,
            )
            
            # Run discovery with terminal goal
            intent, flows, stats = await explorer.run(
                terminal_goal=job.terminal_goal,
                max_flows=job.max_flows,
            )
            
            # Update LLM usage
            await job_manager.update_llm_usage(
                job_id=job_id,
                llm_calls=stats.llm_calls,
                tokens_used=stats.tokens_used,
            )
            
            # Check if cancelled
            job = await job_manager.get_job(job_id)
            if not job or job.cancel_flag:
                await job_manager.send_failed(job_id, "Job cancelled")
                await job_manager.update_job_status(job_id, JobStatus.CANCELLED)
                return
            
            # Convert discovery flows to Axiom format and persist
            backend = await get_backend()
            flow_repo = FlowRepo(backend)
            converter = DiscoveryToAxiomConverter()
            
            created_flows = []
            captured_auth = None
            
            for disc_flow in flows:
                # Convert to Axiom format
                axioms_flow = converter.convert(disc_flow, job.target_url)
                
                # Capture auth session from any auth stage that passed
                for stage in disc_flow.stages:
                    if (
                        stage.status.value == "passed"
                        and stage.captured_auth_session
                        and not captured_auth
                    ):
                        captured_auth = {
                            "captured": True,
                            "flow_type": disc_flow.type,
                            "stage_name": stage.name,
                            "storage_state": stage.captured_auth_session,
                            "message": "Auth session captured - will be auto-applied to future runs",
                        }
                
                # Persist flow
                flow_data = {
                    "project_id": project_id,
                    "name": disc_flow.name,
                    "base_url": job.target_url,
                    "flow_json": axioms_flow,
                }
                
                created_flow_id = await flow_repo.create(**flow_data)
                await job_manager.add_flow_id(job_id, created_flow_id)
                created_flows.append({
                    "id": created_flow_id,
                    "name": disc_flow.name,
                    "step_count": len(axioms_flow.get("steps", [])),
                })
            
            # Store captured auth
            if captured_auth:
                await job_manager.set_captured_auth(job_id, captured_auth)
            
            # Send completion
            await job_manager.send_completed(job_id, created_flows)
            await job_manager.update_job_status(job_id, JobStatus.COMPLETED)
            
        except asyncio.CancelledError:
            await job_manager.send_failed(job_id, "Job cancelled")
            await job_manager.update_job_status(job_id, JobStatus.CANCELLED)
        except Exception as e:
            print(f"[discovery] Job {job_id} failed: {e}")
            await job_manager.send_failed(job_id, str(e))
            await job_manager.update_job_status(job_id, JobStatus.FAILED, error_message=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/usage")
async def get_usage(user_ctx: dict = Depends(get_current_user_context)):
    """Return real usage stats for the authenticated user."""
    user_id = user_ctx["user_id"]
    user_email = user_ctx.get("email") or ""
    backend = await get_backend()
    snapshot = await _build_usage_snapshot(backend, user_id, user_email)

    usage_repo = UsageRepo(backend)
    run_totals = await usage_repo.get_user_run_usage(user_id)

    return {
        "plan_name": snapshot["plan_name"],
        "is_free_tier": snapshot["is_free_tier"],
        "account_enabled": snapshot["account_enabled"],
        "usage_blocked": snapshot["usage_blocked"],
        "max_projects": snapshot["max_projects"],
        "max_runs_per_project": snapshot["max_runs_per_project"],
        "projects_used": snapshot["project_count"],
        "projects_remaining": max(0, snapshot["max_projects"] - snapshot["project_count"]),
        "runs_used_by_project": snapshot["project_run_counts"],
        "total_runs": int(run_totals.get("total_runs") or 0),
        "total_flows": int(run_totals.get("total_flows") or 0),
        "total_compute_hours": round(float(run_totals.get("total_time_ms") or 0) / 3_600_000, 2),
        "max_parallel_workers": MAX_TEST_WORKERS,
        "recording_max_seconds": RECORDING_MAX_SECONDS,
    }


# ── Serve built frontend (Docker / production) ────────────────────
# When AXIOM_SERVE_FRONTEND=1, serve the React build from /app/static.
# This must be the LAST thing mounted so API routes take priority.
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"
if os.environ.get("AXIOM_SERVE_FRONTEND") == "1" and _STATIC_DIR.is_dir():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(_STATIC_DIR / "assets")), name="assets")

    # SPA catch-all: any non-API, non-WS path serves index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API or WebSocket routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")
        # If a real file exists, serve it (favicon, manifest, etc.)
        file_path = _STATIC_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for client-side routing
        return FileResponse(str(_STATIC_DIR / "index.html"))
