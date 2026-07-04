"""
Supabase-backed repository layer.

Mirrors the exact interface of repositories.py but uses the Supabase
PostgREST client instead of SQLite.  JSON/JSONB columns are returned as
native Python dicts — no serialisation needed.  Booleans come back as
True/False.  updated_at is maintained by Postgres triggers.

The service-role client bypasses RLS; access control is still enforced
by passing user_id to every query that owns the row.
"""

import uuid
import re
from datetime import datetime, timezone
from typing import Optional

from supabase import AsyncClient


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── helpers ───────────────────────────────────────────────────────────────

def _cast_bool(v) -> bool:
    """Normalise ints (SQLite) and bools (Supabase) to bool."""
    if isinstance(v, bool):
        return v
    return bool(v)


# ── ProjectRepo ───────────────────────────────────────────────────────────

class ProjectRepo:
    def __init__(self, client: AsyncClient):
        self._sb = client

    @staticmethod
    def _extract_embedded_count(value) -> int:
        if isinstance(value, list):
            if not value:
                return 0
            first = value[0]
            if isinstance(first, dict):
                return int(first.get("count") or 0)
        if isinstance(value, dict):
            return int(value.get("count") or 0)
        if isinstance(value, int):
            return value
        return 0

    async def list_all(self, user_id: Optional[str] = None) -> list[dict]:
        query = (
            self._sb.table("projects")
            .select("id, user_id, name, url, description, validation_goal, created_at, updated_at")
            .order("created_at", desc=True)
        )
        if user_id:
            query = query.eq("user_id", user_id)
        res = await query.execute()
        return res.data or []

    async def list_all_with_stats(self, user_id: str) -> list[dict]:
        query = (
            self._sb.table("projects")
            .select(
                "id, user_id, name, url, description, validation_goal, created_at, updated_at, flows(count), test_runs(count)"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        res = await query.execute()
        rows = res.data or []

        projects: list[dict] = []
        for row in rows:
            flow_count = self._extract_embedded_count(row.get("flows"))
            run_count = self._extract_embedded_count(row.get("test_runs"))
            project = {
                "id": row.get("id"),
                "user_id": row.get("user_id"),
                "name": row.get("name", ""),
                "url": row.get("url", ""),
                "description": row.get("description", ""),
                "validation_goal": row.get("validation_goal", ""),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "stats": {
                    "flow_count": flow_count,
                    "run_count": run_count,
                },
            }
            projects.append(project)
        return projects

    async def get(self, project_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        query = self._sb.table("projects").select("*").eq("id", project_id)
        if user_id:
            query = query.eq("user_id", user_id)
        res = await query.limit(1).execute()
        return res.data[0] if res.data else None

    async def create(
        self,
        name: str,
        url: str = "",
        description: str = "",
        validation_goal: str = "",
        test_config: Optional[dict] = None,
        user_id: str = "dev-user",
    ) -> dict:
        row = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": name,
            "url": url,
            "description": description,
            "validation_goal": validation_goal,
            "test_config_json": test_config or {},
        }
        res = await self._sb.table("projects").insert(row).execute()
        return res.data[0]

    async def update(
        self, project_id: str, user_id: str = "dev-user", **fields
    ) -> Optional[dict]:
        updates: dict = {}
        for k in ("name", "url", "description", "validation_goal"):
            if k in fields:
                updates[k] = fields[k]
        if "test_config_json" in fields:
            updates["test_config_json"] = fields["test_config_json"] or {}
        if not updates:
            return await self.get(project_id, user_id)
        await (
            self._sb.table("projects")
            .update(updates)
            .eq("id", project_id)
            .eq("user_id", user_id)
            .execute()
        )
        return await self.get(project_id, user_id)

    async def delete(self, project_id: str, user_id: str = "dev-user") -> bool:
        res = (
            await self._sb.table("projects")
            .delete()
            .eq("id", project_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(res.data)

    async def get_stats(self, project_id: str) -> dict:
        flows_res = (
            await self._sb.table("flows")
            .select("id", count="exact")
            .eq("project_id", project_id)
            .limit(0)
            .execute()
        )
        runs_res = (
            await self._sb.table("test_runs")
            .select("id", count="exact")
            .eq("project_id", project_id)
            .limit(0)
            .execute()
        )
        flow_count = int((flows_res.count or 0) if hasattr(flows_res, "count") else 0)
        run_count = int((runs_res.count or 0) if hasattr(runs_res, "count") else 0)
        return {
            "flow_count": flow_count,
            "run_count": run_count,
        }


# ── FlowRepo ──────────────────────────────────────────────────────────────

class FlowRepo:
    def __init__(self, client: AsyncClient):
        self._sb = client

    async def list_by_project(
        self, project_id: str, user_id: Optional[str] = None
    ) -> list[dict]:
        query = (
            self._sb.table("flows")
            .select("id, project_id, name, is_mobile, base_url, step_count, created_at, updated_at")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
        )
        if user_id:
            query = query.eq("user_id", user_id)
        res = await query.execute()
        return res.data or []

    async def get(self, flow_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        query = self._sb.table("flows").select("*").eq("id", flow_id)
        if user_id:
            query = query.eq("user_id", user_id)
        res = await query.limit(1).execute()
        return res.data[0] if res.data else None

    async def create(
        self,
        project_id: str,
        name: str,
        base_url: str,
        flow_json: dict,
        recording_artifacts_json: Optional[dict] = None,
        flow_id: Optional[str] = None,
        is_mobile: bool = False,
        user_id: str = "dev-user",
    ) -> dict:
        name = await self._allocate_default_flow_name(project_id, user_id, name)
        row = {
            "id": flow_id or str(uuid.uuid4()),
            "user_id": user_id,
            "project_id": project_id,
            "name": name,
            "is_mobile": bool(is_mobile),
            "base_url": base_url,
            "flow_json": flow_json,
            "recording_artifacts_json": recording_artifacts_json or {},
            "step_count": len(flow_json.get("steps", [])),
        }
        # Upsert: if a flow with this id already exists, update it in place
        res = await self._sb.table("flows").upsert(row, on_conflict="id").execute()
        return res.data[0]

    async def _allocate_default_flow_name(self, project_id: str, user_id: str, name: str) -> str:
        normalized = (name or "").strip()
        if not normalized:
            normalized = "New Flow"

        auto_name_pattern = re.compile(r"^new flow(?:\s+\d+)?$", re.IGNORECASE)
        if normalized.lower() != "untitled" and not auto_name_pattern.match(normalized):
            return normalized

        rows = await self.list_by_project(project_id, user_id)
        max_index = 0
        pattern = re.compile(r"^new flow\s+(\d+)$", re.IGNORECASE)
        for row in rows:
            existing_name = (row.get("name") or "").strip()
            match = pattern.match(existing_name)
            if not match:
                continue
            try:
                max_index = max(max_index, int(match.group(1)))
            except ValueError:
                continue

        return f"New Flow {max_index + 1}"

    async def update(
        self, flow_id: str, user_id: str = "dev-user", **fields
    ) -> Optional[dict]:
        updates: dict = {}
        for k in ("name", "base_url", "is_mobile"):
            if k in fields:
                updates[k] = bool(fields[k]) if k == "is_mobile" else fields[k]
        if "flow_json" in fields:
            fd = fields["flow_json"]
            updates["flow_json"] = fd
            updates["step_count"] = len(fd.get("steps", [])) if isinstance(fd, dict) else 0
        if "recording_artifacts_json" in fields:
            updates["recording_artifacts_json"] = fields["recording_artifacts_json"] or {}
        if not updates:
            return await self.get(flow_id, user_id)
        await (
            self._sb.table("flows")
            .update(updates)
            .eq("id", flow_id)
            .eq("user_id", user_id)
            .execute()
        )
        return await self.get(flow_id, user_id)

    async def delete(self, flow_id: str, user_id: str = "dev-user") -> bool:
        res = (
            await self._sb.table("flows")
            .delete()
            .eq("id", flow_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(res.data)

    async def list_ids_for_user(self, user_id: str) -> list[str]:
        """Return all flow IDs owned by the given user (across all projects)."""
        res = await self._sb.table("flows").select("id").eq("user_id", user_id).execute()
        return [row["id"] for row in (res.data or [])]

    async def list_by_ids(self, flow_ids: list[str], user_id: Optional[str] = None) -> list[dict]:
        if not flow_ids:
            return []
        query = self._sb.table("flows").select("*").in_("id", flow_ids)
        if user_id:
            query = query.eq("user_id", user_id)
        res = await query.execute()
        return res.data or []


# ── TestCaseRepo ──────────────────────────────────────────────────────────

class TestCaseRepo:
    def __init__(self, client: AsyncClient):
        self._sb = client

    async def list_by_flow(
        self, flow_id: str, *, active_only: bool = False
    ) -> list[dict]:
        query = (
            self._sb.table("test_cases")
            .select("*")
            .eq("flow_id", flow_id)
            .order("is_baseline", desc=True)
            .order("created_at")
        )
        if active_only:
            query = query.eq("active", True)
        res = await query.execute()
        return res.data or []

    async def get(self, test_case_id: str) -> Optional[dict]:
        res = (
            await self._sb.table("test_cases")
            .select("*")
            .eq("id", test_case_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    async def upsert_many(self, flow_id: str, cases: list[dict]) -> list[dict]:
        existing_res = (
            await self._sb.table("test_cases").select("*").eq("flow_id", flow_id).execute()
        )
        by_type = {c["variation_type"]: c for c in (existing_res.data or [])}

        result: list[dict] = []
        for case in cases:
            row = {
                "flow_id": flow_id,
                "name": case["name"],
                "variation_type": case["variation_type"],
                "environment_profile": case.get("environment_profile", "normal"),
                "is_baseline": _cast_bool(case.get("is_baseline", False)),
                "active": _cast_bool(case.get("active", True)),
                "applicability_reason": case.get("applicability_reason"),
                "applicability_meta_json": case.get("applicability_meta_json") or {},
                "expected_failure_class": case.get("expected_failure_class"),
                "expected_outcome": case.get("expected_outcome", "pass"),
                "definition_json": case.get("definition_json") or {},
            }
            existing_case = by_type.get(case["variation_type"])
            if existing_case:
                up_res = (
                    await self._sb.table("test_cases")
                    .update(row)
                    .eq("id", existing_case["id"])
                    .execute()
                )
                if up_res.data:
                    result.append(up_res.data[0])
            else:
                row["id"] = str(uuid.uuid4())
                ins_res = await self._sb.table("test_cases").insert(row).execute()
                if ins_res.data:
                    result.append(ins_res.data[0])
        return result

    async def update(self, test_case_id: str, **fields) -> Optional[dict]:
        updates: dict = {}
        for k in (
            "name",
            "variation_type",
            "environment_profile",
            "applicability_reason",
            "expected_failure_class",
            "expected_outcome",
        ):
            if k in fields:
                updates[k] = fields[k]
        for bool_k in ("active", "is_baseline"):
            if bool_k in fields:
                updates[bool_k] = _cast_bool(fields[bool_k])
        for json_k in ("applicability_meta_json", "definition_json"):
            if json_k in fields:
                updates[json_k] = fields[json_k] or {}
        if not updates:
            return await self.get(test_case_id)
        await self._sb.table("test_cases").update(updates).eq("id", test_case_id).execute()
        return await self.get(test_case_id)

    async def delete(self, test_case_id: str) -> bool:
        res = (
            await self._sb.table("test_cases").delete().eq("id", test_case_id).execute()
        )
        return bool(res.data)

    async def delete_by_flow(self, flow_id: str) -> None:
        """Bulk-delete all test cases for a flow (cascade helper)."""
        await self._sb.table("test_cases").delete().eq("flow_id", flow_id).execute()


# ── RunGroupRepo ──────────────────────────────────────────────────────────

class RunGroupRepo:
    def __init__(self, client: AsyncClient):
        self._sb = client

    async def create(
        self, flow_id: str, project_id: str = "", config: Optional[dict] = None
    ) -> dict:
        row = {
            "id": str(uuid.uuid4()),
            "flow_id": flow_id,
            "project_id": project_id or None,
            "status": "pending",
            "config_json": config or {},
        }
        res = await self._sb.table("run_groups").insert(row).execute()
        return res.data[0]

    async def get(self, run_group_id: str) -> Optional[dict]:
        res = (
            await self._sb.table("run_groups")
            .select("*")
            .eq("id", run_group_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    async def list_by_flow(self, flow_id: str, limit: int = 50) -> list[dict]:
        res = (
            await self._sb.table("run_groups")
            .select("*")
            .eq("flow_id", flow_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    async def count_by_project(self, project_id: str) -> int:
        res = (
            await self._sb.table("run_groups")
            .select("id", count="exact")
            .eq("project_id", project_id)
            .limit(0)
            .execute()
        )
        return int((res.count or 0) if hasattr(res, "count") else 0)

    async def counts_by_project(self, project_ids: list[str]) -> dict[str, int]:
        if not project_ids:
            return {}
        res = (
            await self._sb.table("run_groups")
            .select("project_id")
            .in_("project_id", project_ids)
            .execute()
        )
        counts: dict[str, int] = {pid: 0 for pid in project_ids}
        for row in (res.data or []):
            project_id = row.get("project_id")
            if not project_id:
                continue
            counts[project_id] = counts.get(project_id, 0) + 1
        return counts

    async def update_status(
        self, run_group_id: str, status: str, **fields
    ) -> None:
        updates: dict = {"status": status}
        for k in (
            "started_at",
            "finished_at",
            "total_runs",
            "runs_passed",
            "runs_failed",
            "total_time_ms",
        ):
            if k in fields:
                updates[k] = fields[k]
        for int_key in ("total_runs", "runs_passed", "runs_failed", "total_time_ms"):
            if int_key in updates and updates[int_key] is not None:
                updates[int_key] = int(round(float(updates[int_key])))
        await (
            self._sb.table("run_groups")
            .update(updates)
            .eq("id", run_group_id)
            .execute()
        )

    async def list_by_status(self, status: str) -> list[dict]:
        """Return run groups with given status (used for startup stuck-run recovery)."""
        res = (
            await self._sb.table("run_groups").select("id").eq("status", status).execute()
        )
        return res.data or []

    async def delete_by_flow(self, flow_id: str) -> None:
        """Bulk-delete all run groups for a flow (cascade helper)."""
        await self._sb.table("run_groups").delete().eq("flow_id", flow_id).execute()


# ── TestRunRepo ───────────────────────────────────────────────────────────

class TestRunRepo:
    def __init__(self, client: AsyncClient):
        self._sb = client

    async def create(
        self,
        flow_id: str,
        flow_name: str = "",
        project_id: str = "",
        config: Optional[dict] = None,
        run_group_id: Optional[str] = None,
        test_case_id: Optional[str] = None,
        variation_type: str = "baseline",
        environment_profile: str = "normal",
        is_baseline: bool = False,
    ) -> dict:
        row = {
            "id": str(uuid.uuid4()),
            "flow_id": flow_id,
            "flow_name": flow_name,
            "project_id": project_id or None,
            "run_group_id": run_group_id or None,
            "test_case_id": test_case_id or None,
            "variation_type": variation_type,
            "environment_profile": environment_profile,
            "is_baseline": _cast_bool(is_baseline),
            "status": "pending",
            "config_json": config or {},
            "artifacts_json": {},
            "diagnostics_json": {},
            "failure_secondary_signals_json": {},
        }
        res = await self._sb.table("test_runs").insert(row).execute()
        return res.data[0]

    async def get(self, run_id: str) -> Optional[dict]:
        res = (
            await self._sb.table("test_runs")
            .select("*")
            .eq("id", run_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    async def list_all(self, limit: int = 50) -> list[dict]:
        res = (
            await self._sb.table("test_runs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    async def list_by_flow(self, flow_id: str, limit: int = 50) -> list[dict]:
        res = (
            await self._sb.table("test_runs")
            .select("*")
            .eq("flow_id", flow_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    async def list_ids_by_flow(self, flow_id: str) -> list[str]:
        """Return all run IDs for a flow (used for cascade delete)."""
        res = (
            await self._sb.table("test_runs").select("id").eq("flow_id", flow_id).execute()
        )
        return [r["id"] for r in (res.data or [])]

    async def list_by_status(self, status: str) -> list[dict]:
        """Return all runs with a given status (used for startup stuck-run recovery)."""
        res = (
            await self._sb.table("test_runs").select("id").eq("status", status).execute()
        )
        return res.data or []

    async def delete_by_flow(self, flow_id: str) -> None:
        """Bulk-delete all runs for a flow (cascade helper)."""
        await self._sb.table("test_runs").delete().eq("flow_id", flow_id).execute()

    async def list_by_flow_ids(self, flow_ids: list[str], limit: int = 50) -> list[dict]:
        """List runs scoped to a set of flow IDs (used for user-scoped list-all)."""
        if not flow_ids:
            return []
        res = (
            await self._sb.table("test_runs")
            .select("*")
            .in_("flow_id", flow_ids)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    async def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        res = (
            await self._sb.table("test_runs")
            .select("*, flows!inner(user_id)")
            .eq("flows.user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = res.data or []
        for row in rows:
            row.pop("flows", None)
        return rows

    async def aggregate_usage_by_user(self, user_id: str) -> dict:
        res = (
            await self._sb.table("test_runs")
            .select("total_time_ms, flows!inner(user_id)")
            .eq("flows.user_id", user_id)
            .execute()
        )
        rows = res.data or []
        total_runs = len(rows)
        total_time_ms = sum(float(row.get("total_time_ms") or 0) for row in rows)
        return {
            "total_runs": total_runs,
            "total_time_ms": total_time_ms,
        }

    async def list_by_run_group(self, run_group_id: str) -> list[dict]:
        res = (
            await self._sb.table("test_runs")
            .select("*")
            .eq("run_group_id", run_group_id)
            .order("is_baseline", desc=True)
            .order("created_at")
            .execute()
        )
        return res.data or []

    async def update_status(self, run_id: str, status: str, **fields) -> None:
        updates: dict = {"status": status}
        for k in (
            "started_at",
            "finished_at",
            "actions_executed",
            "actions_passed",
            "actions_failed",
            "total_steps",
            "passed_steps",
            "confidence_score",
            "total_time_ms",
            "failure_class",
            "blocked_reason",
            "failure_root_cause",
        ):
            if k in fields:
                updates[k] = fields[k]
        for int_key in (
            "actions_executed",
            "actions_passed",
            "actions_failed",
            "total_steps",
            "passed_steps",
            "total_time_ms",
        ):
            if int_key in updates and updates[int_key] is not None:
                updates[int_key] = int(round(float(updates[int_key])))
        for json_k in ("artifacts_json", "diagnostics_json", "failure_secondary_signals_json"):
            if json_k in fields:
                updates[json_k] = fields[json_k] or {}
        await self._sb.table("test_runs").update(updates).eq("id", run_id).execute()


# ── TestResultRepo ────────────────────────────────────────────────────────

class TestResultRepo:
    def __init__(self, client: AsyncClient):
        self._sb = client

    async def create(
        self,
        run_id: str,
        step_order: int,
        step_id: str = "",
        action_type: str = "",
        target_name: str = "",
        status: str = "pending",
    ) -> dict:
        row = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "step_order": step_order,
            "step_id": step_id,

            "action_type": action_type,
            "target_name": target_name,
            "status": status,
            "attempt_trace_json": [],
            "selection_source": None,
        }
        res = await self._sb.table("test_results").insert(row).execute()
        return res.data[0]

    async def update(self, result_id: str, status: str, **fields) -> None:
        updates: dict = {"status": status}
        for k in (
            "confidence",
            "resolver_path",
            "failure_reason",
            "failure_message",
            "screenshot_path",
            "time_taken_ms",
            "selection_source",
        ):
            if k in fields:
                updates[k] = fields[k]
        if "time_taken_ms" in updates and updates["time_taken_ms"] is not None:
            updates["time_taken_ms"] = int(round(float(updates["time_taken_ms"])))
        if "attempt_trace_json" in fields:
            updates["attempt_trace_json"] = fields["attempt_trace_json"] or []
        await self._sb.table("test_results").update(updates).eq("id", result_id).execute()

    async def list_by_run(self, run_id: str) -> list[dict]:
        res = (
            await self._sb.table("test_results")
            .select("*")
            .eq("run_id", run_id)
            .order("step_order")
            .execute()
        )
        return res.data or []

    async def list_by_runs(self, run_ids: list[str]) -> dict[str, list[dict]]:
        if not run_ids:
            return {}
        res = (
            await self._sb.table("test_results")
            .select("*")
            .in_("run_id", run_ids)
            .order("run_id")
            .order("step_order")
            .execute()
        )
        grouped: dict[str, list[dict]] = {run_id: [] for run_id in run_ids}
        for row in (res.data or []):
            run_id = row.get("run_id")
            if not run_id:
                continue
            grouped.setdefault(run_id, []).append(row)
        return grouped

    async def delete_by_runs(self, run_ids: list[str]) -> None:
        """Bulk-delete all test results for a list of run IDs (cascade helper)."""
        if not run_ids:
            return
        await self._sb.table("test_results").delete().in_("run_id", run_ids).execute()


class UsageRepo:
    """Plan and account usage repository for backend enforcement."""

    def __init__(self, client: AsyncClient):
        self._sb = client

    async def get_plan(self, plan_id: str) -> Optional[dict]:
        res = (
            await self._sb.table("usage_plans")
            .select("*")
            .eq("id", plan_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    async def get_default_plan(self) -> Optional[dict]:
        res = (
            await self._sb.table("usage_plans")
            .select("*")
            .eq("is_default", True)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
        return await self.get_plan("pro_default")

    async def get_free_plan(self) -> Optional[dict]:
        res = (
            await self._sb.table("usage_plans")
            .select("*")
            .eq("is_free_tier", True)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
        return await self.get_plan("free_tier")

    async def get_user_account(self, user_id: str) -> Optional[dict]:
        res = (
            await self._sb.table("user_accounts")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    async def ensure_user_account(self, user_id: str, user_email: str) -> dict:
        account = await self.get_user_account(user_id)
        if account:
            if user_email and account.get("user_email") != user_email:
                updated = (
                    await self._sb.table("user_accounts")
                    .update({"user_email": user_email})
                    .eq("user_id", user_id)
                    .execute()
                )
                if updated.data:
                    return updated.data[0]
            return account

        free_plan = await self.get_free_plan()
        if not free_plan:
            raise RuntimeError("No free usage plan configured")

        row = {
            "user_id": user_id,
            "user_email": user_email or "",
            "plan_id": free_plan["id"],
            "account_enabled": True,
        }
        res = await self._sb.table("user_accounts").insert(row).execute()
        return res.data[0]

    async def get_user_run_usage(self, user_id: str) -> dict:
        res = (
            await self._sb.table("v_user_run_usage")
            .select("total_runs, total_time_ms, total_flows")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        row = res.data[0] if res.data else {}
        return {
            "total_runs": int(row.get("total_runs") or 0),
            "total_time_ms": float(row.get("total_time_ms") or 0),
            "total_flows": int(row.get("total_flows") or 0),
        }
