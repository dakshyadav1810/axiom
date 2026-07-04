"""
Repository factory.

Selects the right backend at import time based on env vars:
  - SUPABASE_SERVICE_ROLE_KEY set → Supabase (PostgreSQL via PostgREST)
  - otherwise               → SQLite (local dev / Docker)

Usage in any module:
    from axiom_recorder.db.repo_factory import (
        get_backend, ProjectRepo, FlowRepo, TestCaseRepo,
        RunGroupRepo, TestRunRepo, TestResultRepo,
    )
    ...
    backend = await get_backend()
    repo    = ProjectRepo(backend)
"""

import os

_USE_SUPABASE: bool = bool(
    os.getenv("SUPABASE_SERVICE_ROLE_KEY") and os.getenv("SUPABASE_URL")
)

if _USE_SUPABASE:
    from .supabase_client import get_supabase_client as get_backend  # noqa: F401
    from .supabase_repos import (  # noqa: F401
        FlowRepo,
        ProjectRepo,
        RunGroupRepo,
        TestCaseRepo,
        TestResultRepo,
        TestRunRepo,
        UsageRepo,
    )
else:
    from .database import get_db as get_backend  # noqa: F401
    from .repositories import (  # noqa: F401
        FlowRepo,
        ProjectRepo,
        RunGroupRepo,
        TestCaseRepo,
        TestResultRepo,
        TestRunRepo,
        UsageRepo,
    )
