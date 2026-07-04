"""
SQLite database connection and schema management.

Auto-creates tables on first use. Uses aiosqlite for async compatibility
with FastAPI.
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import aiosqlite
from dotenv import load_dotenv

load_dotenv()

# Default database path — relative to workspace root, overridable via DB_PATH env
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "axiom_data.db",
)
DB_PATH = os.getenv("DB_PATH") or DEFAULT_DB_PATH


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'dev-user',
    name TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    validation_goal TEXT NOT NULL DEFAULT '',
    test_config_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS flows (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'dev-user',
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    is_mobile INTEGER NOT NULL DEFAULT 0,
    base_url TEXT NOT NULL DEFAULT '',
    flow_json TEXT NOT NULL DEFAULT '{}',
    recording_artifacts_json TEXT NOT NULL DEFAULT '{}',
    step_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_runs (
    id TEXT PRIMARY KEY,
    flow_id TEXT NOT NULL,
    flow_name TEXT NOT NULL DEFAULT '',
    project_id TEXT NOT NULL DEFAULT '',
    run_group_id TEXT,
    test_case_id TEXT,
    variation_type TEXT NOT NULL DEFAULT 'baseline',
    environment_profile TEXT NOT NULL DEFAULT 'normal',
    is_baseline INTEGER NOT NULL DEFAULT 0,
    failure_class TEXT,
    blocked_reason TEXT,
    failure_root_cause TEXT,
    artifacts_json TEXT NOT NULL DEFAULT '{}',
    diagnostics_json TEXT NOT NULL DEFAULT '{}',
    failure_secondary_signals_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    config_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    actions_executed INTEGER NOT NULL DEFAULT 0,
    actions_passed INTEGER NOT NULL DEFAULT 0,
    actions_failed INTEGER NOT NULL DEFAULT 0,
    total_steps INTEGER NOT NULL DEFAULT 0,
    passed_steps INTEGER NOT NULL DEFAULT 0,
    confidence_score REAL,
    total_time_ms INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE,
    FOREIGN KEY (run_group_id) REFERENCES run_groups(id) ON DELETE SET NULL,
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    flow_id TEXT NOT NULL,
    name TEXT NOT NULL,
    variation_type TEXT NOT NULL,
    environment_profile TEXT NOT NULL DEFAULT 'normal',
    is_baseline INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    applicability_reason TEXT,
    applicability_meta_json TEXT NOT NULL DEFAULT '{}',
    expected_failure_class TEXT,
    expected_outcome TEXT NOT NULL DEFAULT 'pass',
    definition_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS run_groups (
    id TEXT PRIMARY KEY,
    flow_id TEXT NOT NULL,
    project_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    config_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    total_runs INTEGER NOT NULL DEFAULT 0,
    runs_passed INTEGER NOT NULL DEFAULT 0,
    runs_failed INTEGER NOT NULL DEFAULT 0,
    total_time_ms INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    step_id TEXT NOT NULL DEFAULT '',
    action_type TEXT NOT NULL DEFAULT '',
    target_name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    confidence REAL,
    resolver_path TEXT,
    failure_reason TEXT,
    failure_message TEXT,
    screenshot_path TEXT,
    attempt_trace_json TEXT NOT NULL DEFAULT '[]',
    selection_source TEXT,
    time_taken_ms INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES test_runs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS usage_plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    max_projects INTEGER NOT NULL,
    max_runs_per_project INTEGER NOT NULL,
    is_free_tier INTEGER NOT NULL DEFAULT 0,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_accounts (
    user_id TEXT PRIMARY KEY,
    user_email TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    account_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES usage_plans(id)
);

CREATE INDEX IF NOT EXISTS idx_flows_project ON flows(project_id);
CREATE INDEX IF NOT EXISTS idx_test_runs_flow ON test_runs(flow_id);
CREATE INDEX IF NOT EXISTS idx_test_results_run ON test_results(run_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_flow ON test_cases(flow_id);
CREATE INDEX IF NOT EXISTS idx_run_groups_flow ON run_groups(flow_id);
CREATE INDEX IF NOT EXISTS idx_user_accounts_plan ON user_accounts(plan_id);
"""


class Database:
    """
    Async SQLite database wrapper.

    Usage:
        db = Database()
        await db.initialize()
        async with db.connection() as conn:
            await conn.execute(...)
        await db.close()
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Open connection and create tables if they don't exist."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._db.executescript(SCHEMA_SQL)
        await self._apply_migrations()
        await self._db.commit()

    async def _ensure_column(self, table: str, column: str, ddl: str) -> None:
        """Add a missing column for backward-compatible schema upgrades."""
        cursor = await self._db.execute(f"PRAGMA table_info({table})")
        rows = await cursor.fetchall()
        existing = {row["name"] for row in rows}
        if column not in existing:
            await self._db.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

    async def _apply_migrations(self) -> None:
        """Run lightweight in-place schema migrations."""
        # user_id columns for multi-tenant isolation
        await self._ensure_column(
            "projects", "user_id", "user_id TEXT NOT NULL DEFAULT 'dev-user'"
        )
        await self._ensure_column(
            "flows", "user_id", "user_id TEXT NOT NULL DEFAULT 'dev-user'"
        )
        await self._ensure_column(
            "projects",
            "test_config_json",
            "test_config_json TEXT NOT NULL DEFAULT '{}'",
        )
        await self._ensure_column(
            "projects",
            "validation_goal",
            "validation_goal TEXT NOT NULL DEFAULT ''",
        )
        await self._ensure_column("test_runs", "run_group_id", "run_group_id TEXT")
        await self._ensure_column("test_runs", "test_case_id", "test_case_id TEXT")
        await self._ensure_column(
            "test_runs",
            "variation_type",
            "variation_type TEXT NOT NULL DEFAULT 'baseline'",
        )
        await self._ensure_column(
            "test_runs",
            "environment_profile",
            "environment_profile TEXT NOT NULL DEFAULT 'normal'",
        )
        await self._ensure_column(
            "test_runs",
            "is_baseline",
            "is_baseline INTEGER NOT NULL DEFAULT 0",
        )
        await self._ensure_column("test_runs", "failure_class", "failure_class TEXT")
        await self._ensure_column("test_runs", "blocked_reason", "blocked_reason TEXT")
        await self._ensure_column("test_runs", "failure_root_cause", "failure_root_cause TEXT")
        await self._ensure_column(
            "test_runs",
            "artifacts_json",
            "artifacts_json TEXT NOT NULL DEFAULT '{}'",
        )
        await self._ensure_column(
            "test_runs",
            "diagnostics_json",
            "diagnostics_json TEXT NOT NULL DEFAULT '{}'",
        )
        await self._ensure_column(
            "test_runs",
            "failure_secondary_signals_json",
            "failure_secondary_signals_json TEXT NOT NULL DEFAULT '{}'",
        )
        await self._ensure_column(
            "test_runs",
            "total_steps",
            "total_steps INTEGER NOT NULL DEFAULT 0",
        )
        await self._ensure_column(
            "test_runs",
            "passed_steps",
            "passed_steps INTEGER NOT NULL DEFAULT 0",
        )
        await self._ensure_column(
            "test_runs",
            "confidence_score",
            "confidence_score REAL",
        )
        await self._ensure_column(
            "flows",
            "recording_artifacts_json",
            "recording_artifacts_json TEXT NOT NULL DEFAULT '{}'",
        )
        await self._ensure_column(
            "flows",
            "is_mobile",
            "is_mobile INTEGER NOT NULL DEFAULT 0",
        )
        await self._ensure_column(
            "test_cases",
            "applicability_meta_json",
            "applicability_meta_json TEXT NOT NULL DEFAULT '{}'",
        )
        await self._ensure_column(
            "test_results",
            "attempt_trace_json",
            "attempt_trace_json TEXT NOT NULL DEFAULT '[]'",
        )
        await self._ensure_column(
            "test_results",
            "selection_source",
            "selection_source TEXT",
        )
        await self._ensure_column(
            "test_cases",
            "expected_outcome",
            "expected_outcome TEXT NOT NULL DEFAULT 'pass'",
        )
        await self._ensure_column(
            "user_accounts",
            "user_email",
            "user_email TEXT NOT NULL DEFAULT ''",
        )
        await self._ensure_column(
            "user_accounts",
            "plan_id",
            "plan_id TEXT NOT NULL DEFAULT 'free_tier'",
        )
        await self._ensure_column(
            "user_accounts",
            "account_enabled",
            "account_enabled INTEGER NOT NULL DEFAULT 1",
        )
        await self._seed_usage_plans()
        await self._create_indexes()

    async def _seed_usage_plans(self) -> None:
        """Ensure built-in plans exist and are editable from DB afterwards."""
        now = _now_iso()
        await self._db.execute(
            """
            INSERT OR IGNORE INTO usage_plans
            (id, name, max_projects, max_runs_per_project, is_free_tier, is_default, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("free_tier", "Free Tier", 1, 3, 1, 0, now, now),
        )
        await self._db.execute(
            """
            INSERT OR IGNORE INTO usage_plans
            (id, name, max_projects, max_runs_per_project, is_free_tier, is_default, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("pro_default", "Pro", 3, 10, 0, 1, now, now),
        )

    async def _create_indexes(self) -> None:
        """Create indexes that depend on migrated columns."""
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_runs_run_group ON test_runs(run_group_id)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_runs_flow_created ON test_runs(flow_id, created_at DESC)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_runs_group_baseline_created ON test_runs(run_group_id, is_baseline DESC, created_at ASC)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_runs_test_case ON test_runs(test_case_id)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_test_results_run_step_order ON test_results(run_id, step_order)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_run_groups_project_created ON run_groups(project_id, created_at DESC)"
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_flows_project_created ON flows(project_id, created_at DESC)"
        )

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def conn(self) -> aiosqlite.Connection:
        """Get the active connection. Raises if not initialized."""
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._db


# Singleton instance
_db_instance: Optional[Database] = None


async def get_db() -> Database:
    """Get or create the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        await _db_instance.initialize()
    return _db_instance
