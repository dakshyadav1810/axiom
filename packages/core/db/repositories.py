"""
Repository layer for CRUD operations on projects, flows, test runs/results,
flow test-cases, and run groups.

All methods are async and use the shared Database connection.
"""

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from .database import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads_json(value, default):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _hydrate_run(row: dict) -> dict:
    row["config_json"] = _loads_json(row.get("config_json"), {})
    row["artifacts_json"] = _loads_json(row.get("artifacts_json"), {})
    row["diagnostics_json"] = _loads_json(row.get("diagnostics_json"), {})
    row["failure_secondary_signals_json"] = _loads_json(
        row.get("failure_secondary_signals_json"),
        {},
    )
    row["is_baseline"] = bool(row.get("is_baseline", 0))
    return row


def _hydrate_project(row: dict) -> dict:
    row["test_config_json"] = _loads_json(row.get("test_config_json"), {})
    return row


def _hydrate_test_case(row: dict) -> dict:
    row["definition_json"] = _loads_json(row.get("definition_json"), {})
    row["applicability_meta_json"] = _loads_json(row.get("applicability_meta_json"), {})
    row["active"] = bool(row.get("active", 0))
    row["is_baseline"] = bool(row.get("is_baseline", 0))
    return row


def _hydrate_flow(row: dict) -> dict:
    row["flow_json"] = _loads_json(row.get("flow_json"), {})
    row["recording_artifacts_json"] = _loads_json(row.get("recording_artifacts_json"), {})
    row["is_mobile"] = bool(row.get("is_mobile", 0))
    return row


def _hydrate_result(row: dict) -> dict:
    row["attempt_trace_json"] = _loads_json(row.get("attempt_trace_json"), [])
    return row


class ProjectRepo:
    """CRUD operations for projects."""

    def __init__(self, db: Database):
        self.db = db

    async def list_all(self, user_id: str = "dev-user") -> list[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [_hydrate_project(dict(r)) for r in rows]

    async def list_all_with_stats(self, user_id: str = "dev-user") -> list[dict]:
        cursor = await self.db.conn.execute(
            """
            SELECT
                p.*,
                COALESCE(f.flow_count, 0) AS flow_count,
                COALESCE(r.run_count, 0) AS run_count
            FROM projects p
            LEFT JOIN (
                SELECT project_id, COUNT(*) AS flow_count
                FROM flows
                GROUP BY project_id
            ) f ON f.project_id = p.id
            LEFT JOIN (
                SELECT project_id, COUNT(*) AS run_count
                FROM test_runs
                GROUP BY project_id
            ) r ON r.project_id = p.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        projects: list[dict] = []
        for row in rows:
            project = _hydrate_project(dict(row))
            project["stats"] = {
                "flow_count": int(row["flow_count"] or 0),
                "run_count": int(row["run_count"] or 0),
            }
            projects.append(project)
        return projects

    async def get(self, project_id: str, user_id: str = "dev-user") -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
        )
        row = await cursor.fetchone()
        return _hydrate_project(dict(row)) if row else None

    async def create(
        self,
        name: str,
        url: str = "",
        description: str = "",
        validation_goal: str = "",
        test_config: Optional[dict] = None,
        user_id: str = "dev-user",
    ) -> dict:
        project_id = str(uuid.uuid4())
        now = _now_iso()
        test_config_json = json.dumps(test_config or {})
        await self.db.conn.execute(
            "INSERT INTO projects (id, user_id, name, url, description, validation_goal, test_config_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, user_id, name, url, description, validation_goal, test_config_json, now, now),
        )
        await self.db.conn.commit()
        return {
            "id": project_id,
            "user_id": user_id,
            "name": name,
            "url": url,
            "description": description,
            "validation_goal": validation_goal,
            "test_config_json": test_config or {},
            "created_at": now,
            "updated_at": now,
        }

    async def update(self, project_id: str, user_id: str = "dev-user", **fields) -> Optional[dict]:
        if not fields:
            return await self.get(project_id, user_id)

        set_clauses = []
        values = []
        for key in ("name", "url", "description", "validation_goal"):
            if key in fields:
                set_clauses.append(f"{key} = ?")
                values.append(fields[key])

        if "test_config_json" in fields:
            set_clauses.append("test_config_json = ?")
            values.append(json.dumps(fields["test_config_json"] or {}))

        if not set_clauses:
            return await self.get(project_id, user_id)

        set_clauses.append("updated_at = ?")
        values.append(_now_iso())
        values.extend([project_id, user_id])

        await self.db.conn.execute(
            f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?",
            tuple(values),
        )
        await self.db.conn.commit()
        return await self.get(project_id, user_id)

    async def delete(self, project_id: str, user_id: str = "dev-user") -> bool:
        cursor = await self.db.conn.execute(
            "DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
        )
        await self.db.conn.commit()
        return cursor.rowcount > 0

    async def get_stats(self, project_id: str) -> dict:
        cursor = await self.db.conn.execute(
            "SELECT COUNT(*) as flow_count FROM flows WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        flow_count = row["flow_count"] if row else 0

        cursor = await self.db.conn.execute(
            "SELECT COUNT(*) as run_count FROM test_runs WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        run_count = row["run_count"] if row else 0

        return {"flow_count": flow_count, "run_count": run_count}


class FlowRepo:
    """CRUD operations for flows."""

    def __init__(self, db: Database):
        self.db = db

    async def list_by_project(self, project_id: str, user_id: str = "dev-user") -> list[dict]:
        cursor = await self.db.conn.execute(
            "SELECT id, project_id, name, is_mobile, base_url, step_count, created_at, updated_at FROM flows WHERE project_id = ? AND user_id = ? ORDER BY created_at DESC",
            (project_id, user_id),
        )
        rows = await cursor.fetchall()
        return [{**dict(r), "is_mobile": bool(dict(r).get("is_mobile", 0))} for r in rows]

    async def list_ids_for_user(self, user_id: str) -> list[str]:
        cursor = await self.db.conn.execute(
            "SELECT id FROM flows WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [row["id"] for row in rows]

    async def list_by_ids(self, flow_ids: list[str], user_id: str = "dev-user") -> list[dict]:
        if not flow_ids:
            return []
        placeholders = ",".join("?" for _ in flow_ids)
        cursor = await self.db.conn.execute(
            f"SELECT * FROM flows WHERE id IN ({placeholders}) AND user_id = ?",
            tuple(flow_ids) + (user_id,),
        )
        rows = await cursor.fetchall()
        return [_hydrate_flow(dict(row)) for row in rows]

    async def get(self, flow_id: str, user_id: str = "dev-user") -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM flows WHERE id = ? AND user_id = ?", (flow_id, user_id)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return _hydrate_flow(dict(row))

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
        fid = flow_id or str(uuid.uuid4())
        now = _now_iso()
        step_count = len(flow_json.get("steps", []))
        flow_json_str = json.dumps(flow_json)
        recording_artifacts_str = json.dumps(recording_artifacts_json or {})

        await self.db.conn.execute(
            """
            INSERT INTO flows
            (id, user_id, project_id, name, is_mobile, base_url, flow_json, recording_artifacts_json, step_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fid,
                user_id,
                project_id,
                name,
                1 if is_mobile else 0,
                base_url,
                flow_json_str,
                recording_artifacts_str,
                step_count,
                now,
                now,
            ),
        )
        await self.db.conn.commit()
        return {
            "id": fid,
            "user_id": user_id,
            "project_id": project_id,
            "name": name,
            "is_mobile": bool(is_mobile),
            "base_url": base_url,
            "step_count": step_count,
            "flow_json": flow_json,
            "recording_artifacts_json": recording_artifacts_json or {},
            "created_at": now,
            "updated_at": now,
        }

    async def _allocate_default_flow_name(self, project_id: str, user_id: str, name: str) -> str:
        normalized = (name or "").strip()
        if not normalized:
            normalized = "New Flow"

        auto_name_pattern = re.compile(r"^new flow(?:\s+\d+)?$", re.IGNORECASE)
        if normalized.lower() != "untitled" and not auto_name_pattern.match(normalized):
            return normalized

        cursor = await self.db.conn.execute(
            "SELECT name FROM flows WHERE project_id = ? AND user_id = ?",
            (project_id, user_id),
        )
        rows = await cursor.fetchall()

        max_index = 0
        pattern = re.compile(r"^new flow\s+(\d+)$", re.IGNORECASE)
        for row in rows:
            existing_name = (row["name"] or "").strip()
            match = pattern.match(existing_name)
            if not match:
                continue
            try:
                max_index = max(max_index, int(match.group(1)))
            except ValueError:
                continue

        return f"New Flow {max_index + 1}"

    async def update(self, flow_id: str, user_id: str = "dev-user", **fields) -> Optional[dict]:
        if not fields:
            return await self.get(flow_id, user_id)

        set_clauses = []
        values = []

        for key in ("name", "base_url"):
            if key in fields:
                set_clauses.append(f"{key} = ?")
                values.append(fields[key])

        if "is_mobile" in fields:
            set_clauses.append("is_mobile = ?")
            values.append(1 if bool(fields["is_mobile"]) else 0)

        if "flow_json" in fields:
            flow_data = fields["flow_json"]
            set_clauses.append("flow_json = ?")
            values.append(json.dumps(flow_data) if isinstance(flow_data, dict) else flow_data)
            set_clauses.append("step_count = ?")
            values.append(len(flow_data.get("steps", [])) if isinstance(flow_data, dict) else 0)
        if "recording_artifacts_json" in fields:
            set_clauses.append("recording_artifacts_json = ?")
            values.append(json.dumps(fields["recording_artifacts_json"] or {}))

        if not set_clauses:
            return await self.get(flow_id, user_id)

        set_clauses.append("updated_at = ?")
        values.append(_now_iso())
        values.extend([flow_id, user_id])

        await self.db.conn.execute(
            f"UPDATE flows SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?",
            tuple(values),
        )
        await self.db.conn.commit()
        return await self.get(flow_id, user_id)

    async def delete(self, flow_id: str, user_id: str = "dev-user") -> bool:
        cursor = await self.db.conn.execute(
            "DELETE FROM flows WHERE id = ? AND user_id = ?", (flow_id, user_id)
        )
        await self.db.conn.commit()
        return cursor.rowcount > 0


class TestCaseRepo:
    """CRUD operations for generated flow test-cases."""

    def __init__(self, db: Database):
        self.db = db

    async def list_by_flow(self, flow_id: str, *, active_only: bool = False) -> list[dict]:
        where = "WHERE flow_id = ?"
        params: list[object] = [flow_id]
        if active_only:
            where += " AND active = 1"
        cursor = await self.db.conn.execute(
            f"""
            SELECT * FROM test_cases
            {where}
            ORDER BY is_baseline DESC, created_at ASC
            """,
            tuple(params),
        )
        rows = await cursor.fetchall()
        return [_hydrate_test_case(dict(row)) for row in rows]

    async def get(self, test_case_id: str) -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM test_cases WHERE id = ?",
            (test_case_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return _hydrate_test_case(dict(row))

    async def upsert_many(self, flow_id: str, cases: list[dict]) -> list[dict]:
        existing = await self.list_by_flow(flow_id)
        by_type = {c["variation_type"]: c for c in existing}
        now = _now_iso()
        created: list[dict] = []

        for case in cases:
            existing_case = by_type.get(case["variation_type"])
            payload = (
                flow_id,
                case["name"],
                case["variation_type"],
                case.get("environment_profile", "normal"),
                1 if case.get("is_baseline") else 0,
                1 if case.get("active", True) else 0,
                case.get("applicability_reason"),
                json.dumps(case.get("applicability_meta_json", {})),
                case.get("expected_failure_class"),
                case.get("expected_outcome", "pass"),
                json.dumps(case.get("definition_json", {})),
                now,
                now,
            )
            if existing_case:
                await self.db.conn.execute(
                    """
                    UPDATE test_cases
                    SET name = ?, variation_type = ?, environment_profile = ?, is_baseline = ?,
                        active = ?, applicability_reason = ?, applicability_meta_json = ?,
                        expected_failure_class = ?, expected_outcome = ?,
                        definition_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        case["name"],
                        case["variation_type"],
                        case.get("environment_profile", "normal"),
                        1 if case.get("is_baseline") else 0,
                        1 if case.get("active", True) else 0,
                        case.get("applicability_reason"),
                        json.dumps(case.get("applicability_meta_json", {})),
                        case.get("expected_failure_class"),
                        case.get("expected_outcome", "pass"),
                        json.dumps(case.get("definition_json", {})),
                        now,
                        existing_case["id"],
                    ),
                )
                created.append(await self.get(existing_case["id"]))
            else:
                test_case_id = str(uuid.uuid4())
                await self.db.conn.execute(
                    """
                    INSERT INTO test_cases
                    (id, flow_id, name, variation_type, environment_profile, is_baseline,
                     active, applicability_reason, applicability_meta_json, expected_failure_class,
                     expected_outcome, definition_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (test_case_id, *payload),
                )
                created.append(await self.get(test_case_id))

        await self.db.conn.commit()
        return [c for c in created if c]

    async def update(self, test_case_id: str, **fields) -> Optional[dict]:
        if not fields:
            return await self.get(test_case_id)

        set_clauses = []
        values = []
        for key in (
            "name",
            "variation_type",
            "environment_profile",
            "applicability_reason",
            "expected_failure_class",
            "expected_outcome",
        ):
            if key in fields:
                set_clauses.append(f"{key} = ?")
                values.append(fields[key])

        if "applicability_meta_json" in fields:
            set_clauses.append("applicability_meta_json = ?")
            values.append(json.dumps(fields["applicability_meta_json"] or {}))

        if "active" in fields:
            set_clauses.append("active = ?")
            values.append(1 if fields["active"] else 0)

        if "is_baseline" in fields:
            set_clauses.append("is_baseline = ?")
            values.append(1 if fields["is_baseline"] else 0)

        if "definition_json" in fields:
            set_clauses.append("definition_json = ?")
            values.append(json.dumps(fields["definition_json"] or {}))

        if not set_clauses:
            return await self.get(test_case_id)

        set_clauses.append("updated_at = ?")
        values.append(_now_iso())
        values.append(test_case_id)

        await self.db.conn.execute(
            f"UPDATE test_cases SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(values),
        )
        await self.db.conn.commit()
        return await self.get(test_case_id)

    async def delete(self, test_case_id: str) -> bool:
        cursor = await self.db.conn.execute(
            "DELETE FROM test_cases WHERE id = ?",
            (test_case_id,),
        )
        await self.db.conn.commit()
        return cursor.rowcount > 0


class RunGroupRepo:
    """CRUD operations for run groups (a batch of test-case runs)."""

    def __init__(self, db: Database):
        self.db = db

    async def create(self, flow_id: str, project_id: str = "", config: Optional[dict] = None) -> dict:
        run_group_id = str(uuid.uuid4())
        now = _now_iso()
        await self.db.conn.execute(
            """
            INSERT INTO run_groups
            (id, flow_id, project_id, status, config_json, created_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (run_group_id, flow_id, project_id, json.dumps(config or {}), now),
        )
        await self.db.conn.commit()
        return {
            "id": run_group_id,
            "flow_id": flow_id,
            "project_id": project_id,
            "status": "pending",
            "config_json": config or {},
            "created_at": now,
            "started_at": None,
            "finished_at": None,
            "total_runs": 0,
            "runs_passed": 0,
            "runs_failed": 0,
            "total_time_ms": 0,
        }

    async def get(self, run_group_id: str) -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM run_groups WHERE id = ?", (run_group_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["config_json"] = _loads_json(d.get("config_json"), {})
        return d

    async def list_by_flow(self, flow_id: str, limit: int = 50) -> list[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM run_groups WHERE flow_id = ? ORDER BY created_at DESC LIMIT ?",
            (flow_id, limit),
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["config_json"] = _loads_json(d.get("config_json"), {})
            result.append(d)
        return result

    async def count_by_project(self, project_id: str) -> int:
        cursor = await self.db.conn.execute(
            "SELECT COUNT(*) AS count FROM run_groups WHERE project_id = ?",
            (project_id,),
        )
        row = await cursor.fetchone()
        return int(row["count"] if row else 0)

    async def counts_by_project(self, project_ids: list[str]) -> dict[str, int]:
        if not project_ids:
            return {}
        placeholders = ",".join("?" for _ in project_ids)
        cursor = await self.db.conn.execute(
            f"""
            SELECT project_id, COUNT(*) AS count
            FROM run_groups
            WHERE project_id IN ({placeholders})
            GROUP BY project_id
            """,
            tuple(project_ids),
        )
        rows = await cursor.fetchall()
        counts: dict[str, int] = {project_id: 0 for project_id in project_ids}
        for row in rows:
            counts[row["project_id"]] = int(row["count"] or 0)
        return counts

    async def update_status(self, run_group_id: str, status: str, **fields) -> None:
        set_clauses = ["status = ?"]
        values = [status]
        int_fields = {"total_runs", "runs_passed", "runs_failed", "total_time_ms"}
        for key in (
            "started_at",
            "finished_at",
            "total_runs",
            "runs_passed",
            "runs_failed",
            "total_time_ms",
        ):
            if key in fields:
                set_clauses.append(f"{key} = ?")
                value = fields[key]
                if key in int_fields and value is not None:
                    value = int(round(float(value)))
                values.append(value)

        values.append(run_group_id)
        await self.db.conn.execute(
            f"UPDATE run_groups SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(values),
        )
        await self.db.conn.commit()


class TestRunRepo:
    """CRUD operations for test runs."""

    def __init__(self, db: Database):
        self.db = db

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
        run_id = str(uuid.uuid4())
        now = _now_iso()
        config_json = json.dumps(config or {})

        await self.db.conn.execute(
            """
            INSERT INTO test_runs
            (id, flow_id, flow_name, project_id, run_group_id, test_case_id,
             variation_type, environment_profile, is_baseline, status, blocked_reason,
             failure_root_cause, config_json, artifacts_json, diagnostics_json,
             failure_secondary_signals_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL, ?, '{}', '{}', '{}', ?)
            """,
            (
                run_id,
                flow_id,
                flow_name,
                project_id,
                run_group_id,
                test_case_id,
                variation_type,
                environment_profile,
                1 if is_baseline else 0,
                config_json,
                now,
            ),
        )
        await self.db.conn.commit()
        return {
            "id": run_id,
            "flow_id": flow_id,
            "flow_name": flow_name,
            "project_id": project_id,
            "run_group_id": run_group_id,
            "test_case_id": test_case_id,
            "variation_type": variation_type,
            "environment_profile": environment_profile,
            "is_baseline": is_baseline,
            "failure_class": None,
            "blocked_reason": None,
            "failure_root_cause": None,
            "artifacts_json": {},
            "diagnostics_json": {},
            "failure_secondary_signals_json": {},
            "status": "pending",
            "config_json": config or {},
            "created_at": now,
            "started_at": None,
            "finished_at": None,
            "actions_executed": 0,
            "actions_passed": 0,
            "actions_failed": 0,
            "total_steps": 0,
            "passed_steps": 0,
            "confidence_score": None,
            "total_time_ms": 0,
        }

    async def get(self, run_id: str) -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM test_runs WHERE id = ?", (run_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return _hydrate_run(dict(row))

    async def list_all(self, limit: int = 50) -> list[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM test_runs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [_hydrate_run(dict(r)) for r in rows]

    async def list_by_flow(self, flow_id: str, limit: int = 50) -> list[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM test_runs WHERE flow_id = ? ORDER BY created_at DESC LIMIT ?",
            (flow_id, limit),
        )
        rows = await cursor.fetchall()
        return [_hydrate_run(dict(r)) for r in rows]

    async def list_by_flow_ids(self, flow_ids: list[str], limit: int = 50) -> list[dict]:
        if not flow_ids:
            return []
        placeholders = ",".join("?" for _ in flow_ids)
        cursor = await self.db.conn.execute(
            f"SELECT * FROM test_runs WHERE flow_id IN ({placeholders}) ORDER BY created_at DESC LIMIT ?",
            tuple(flow_ids) + (limit,),
        )
        rows = await cursor.fetchall()
        return [_hydrate_run(dict(r)) for r in rows]

    async def list_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        cursor = await self.db.conn.execute(
            """
            SELECT tr.*
            FROM test_runs tr
            JOIN flows f ON f.id = tr.flow_id
            WHERE f.user_id = ?
            ORDER BY tr.created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [_hydrate_run(dict(r)) for r in rows]

    async def aggregate_usage_by_user(self, user_id: str) -> dict:
        cursor = await self.db.conn.execute(
            """
            SELECT
                COUNT(tr.id) AS total_runs,
                COALESCE(SUM(tr.total_time_ms), 0) AS total_time_ms
            FROM test_runs tr
            JOIN flows f ON f.id = tr.flow_id
            WHERE f.user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return {
            "total_runs": int(row["total_runs"] or 0) if row else 0,
            "total_time_ms": float(row["total_time_ms"] or 0) if row else 0.0,
        }

    async def list_by_run_group(self, run_group_id: str) -> list[dict]:
        cursor = await self.db.conn.execute(
            """
            SELECT * FROM test_runs
            WHERE run_group_id = ?
            ORDER BY is_baseline DESC, created_at ASC
            """,
            (run_group_id,),
        )
        rows = await cursor.fetchall()
        return [_hydrate_run(dict(r)) for r in rows]

    async def update_status(self, run_id: str, status: str, **fields) -> None:
        set_clauses = ["status = ?"]
        values = [status]
        int_fields = {
            "actions_executed",
            "actions_passed",
            "actions_failed",
            "total_steps",
            "passed_steps",
            "total_time_ms",
        }

        for key in (
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
            if key in fields:
                set_clauses.append(f"{key} = ?")
                value = fields[key]
                if key in int_fields and value is not None:
                    value = int(round(float(value)))
                values.append(value)

        if "artifacts_json" in fields:
            set_clauses.append("artifacts_json = ?")
            values.append(json.dumps(fields["artifacts_json"] or {}))
        if "diagnostics_json" in fields:
            set_clauses.append("diagnostics_json = ?")
            values.append(json.dumps(fields["diagnostics_json"] or {}))
        if "failure_secondary_signals_json" in fields:
            set_clauses.append("failure_secondary_signals_json = ?")
            values.append(json.dumps(fields["failure_secondary_signals_json"] or {}))

        values.append(run_id)
        await self.db.conn.execute(
            f"UPDATE test_runs SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(values),
        )
        await self.db.conn.commit()


class TestResultRepo:
    """CRUD operations for individual step results within a test run."""

    def __init__(self, db: Database):
        self.db = db

    async def create(
        self,
        run_id: str,
        step_order: int,
        step_id: str = "",
        action_type: str = "",
        target_name: str = "",
        status: str = "pending",
    ) -> dict:
        result_id = str(uuid.uuid4())
        now = _now_iso()

        await self.db.conn.execute(
            """
            INSERT INTO test_results
            (id, run_id, step_order, step_id, action_type, target_name, status, attempt_trace_json, selection_source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, '[]', NULL, ?)
            """,
            (result_id, run_id, step_order, step_id, action_type, target_name, status, now),
        )
        await self.db.conn.commit()
        return {
            "id": result_id,
            "run_id": run_id,
            "step_order": step_order,
            "step_id": step_id,
            "action_type": action_type,
            "target_name": target_name,
            "status": status,
            "attempt_trace_json": [],
            "selection_source": None,
        }

    async def update(self, result_id: str, status: str, **fields) -> None:
        set_clauses = ["status = ?"]
        values = [status]

        for key in (
            "confidence",
            "resolver_path",
            "failure_reason",
            "failure_message",
            "screenshot_path",
            "time_taken_ms",
            "selection_source",
        ):
            if key in fields:
                set_clauses.append(f"{key} = ?")
                value = fields[key]
                if key == "time_taken_ms" and value is not None:
                    value = int(round(float(value)))
                values.append(value)
        if "attempt_trace_json" in fields:
            set_clauses.append("attempt_trace_json = ?")
            values.append(json.dumps(fields["attempt_trace_json"] or []))

        values.append(result_id)
        await self.db.conn.execute(
            f"UPDATE test_results SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(values),
        )
        await self.db.conn.commit()

    async def list_by_run(self, run_id: str) -> list[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM test_results WHERE run_id = ? ORDER BY step_order ASC",
            (run_id,),
        )
        rows = await cursor.fetchall()
        return [_hydrate_result(dict(r)) for r in rows]

    async def list_by_runs(self, run_ids: list[str]) -> dict[str, list[dict]]:
        if not run_ids:
            return {}
        placeholders = ",".join("?" for _ in run_ids)
        cursor = await self.db.conn.execute(
            f"SELECT * FROM test_results WHERE run_id IN ({placeholders}) ORDER BY run_id ASC, step_order ASC",
            tuple(run_ids),
        )
        rows = await cursor.fetchall()
        grouped: dict[str, list[dict]] = {run_id: [] for run_id in run_ids}
        for row in rows:
            hydrated = _hydrate_result(dict(row))
            grouped.setdefault(hydrated["run_id"], []).append(hydrated)
        return grouped


class UsageRepo:
    """Plan and account usage repository for backend enforcement."""

    def __init__(self, db: Database):
        self.db = db

    async def get_plan(self, plan_id: str) -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM usage_plans WHERE id = ?",
            (plan_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_default_plan(self) -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM usage_plans WHERE is_default = 1 LIMIT 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else await self.get_plan("pro_default")

    async def get_free_plan(self) -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM usage_plans WHERE is_free_tier = 1 LIMIT 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else await self.get_plan("free_tier")

    async def get_user_account(self, user_id: str) -> Optional[dict]:
        cursor = await self.db.conn.execute(
            "SELECT * FROM user_accounts WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def ensure_user_account(self, user_id: str, user_email: str) -> dict:
        account = await self.get_user_account(user_id)
        if account:
            if user_email and account.get("user_email") != user_email:
                await self.db.conn.execute(
                    "UPDATE user_accounts SET user_email = ?, updated_at = ? WHERE user_id = ?",
                    (user_email, _now_iso(), user_id),
                )
                await self.db.conn.commit()
                account["user_email"] = user_email
            return account

        free_plan = await self.get_free_plan()
        if not free_plan:
            raise RuntimeError("No free usage plan configured")

        now = _now_iso()
        account = {
            "user_id": user_id,
            "user_email": user_email or "",
            "plan_id": free_plan["id"],
            "account_enabled": 1,
            "created_at": now,
            "updated_at": now,
        }
        await self.db.conn.execute(
            """
            INSERT OR REPLACE INTO user_accounts
            (user_id, user_email, plan_id, account_enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                account["user_id"],
                account["user_email"],
                account["plan_id"],
                account["account_enabled"],
                account["created_at"],
                account["updated_at"],
            ),
        )
        await self.db.conn.commit()
        return account

    async def get_user_run_usage(self, user_id: str) -> dict:
        cursor = await self.db.conn.execute(
            """
            SELECT
                COUNT(tr.id) AS total_runs,
                COALESCE(SUM(tr.total_time_ms), 0) AS total_time_ms,
                COUNT(DISTINCT f.id) AS total_flows
            FROM flows f
            LEFT JOIN test_runs tr ON tr.flow_id = f.id
            WHERE f.user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return {
            "total_runs": int(row["total_runs"] or 0) if row else 0,
            "total_time_ms": float(row["total_time_ms"] or 0) if row else 0.0,
            "total_flows": int(row["total_flows"] or 0) if row else 0,
        }
