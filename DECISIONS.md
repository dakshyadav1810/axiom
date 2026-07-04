# Architectural Decisions Log

This document tracks specific engineering decisions made during the migration of the Axiom project to the `packages/core` architecture.

## 1. Split Monolithic Recorder into Feature Domains (2026-07-04)

**Context:** The old repository contained an `axiom_recorder` directory that, despite its name, housed the entire backend (FastAPI server, SQLAlchemy db, execution engine, and recording logic).

**Decision:** Instead of copying the entire directory into `packages/core/recorder`, the monolithic structure was split into its proper feature domains to align with the HLD v3.1:
- `core/recorder`: Only StateAwareRecorder, DOM snapshots, and Playwright interaction observers.
- `core/execution`: Playwright test engine and test generators.
- `core/server`: FastAPI API layer.
- `core/db`: SQLAlchemy storage layer.

**Rationale:** The HLD strictly specifies a modular platform with separation of concerns. This split ensures the backend is feature-based and highly decoupled, preventing circular dependencies.

## 2. Shared Models as Source of Truth (2026-07-04)

**Context:** Both `axiom_recorder` and `axiom-resolvers` had duplicate definitions for models like `DOMElement` and `ActionNode`.

**Decision:** A centralized `packages/core/models/` module was established to house all Pydantic schemas and dataclasses.

**Rationale:** Unified execution (UI vs. API) requires a single source of truth for test definitions.

## 3. Removal of `sys.path` Injection for Resolvers (2026-07-04)

**Context:** The old execution engine used a hack (`sys.path.insert(0, _RESOLVERS_DIR)`) to dynamically inject the `axiom-resolvers` package at runtime.

**Decision:** The resolvers and execution engine were co-located within the single `core` package (`core.resolvers` and `core.execution`), and the `sys.path` hack was replaced with standard relative package imports.

**Rationale:** Dynamic path injection breaks static type checking, makes testing brittle, and violates standard Python packaging conventions.

## 4. Consolidated Dependencies in `axiom-core` (2026-07-04)

**Context:** The old setup relied on a `pyproject.toml` for the API and a separate `requirements.txt` for the resolvers.

**Decision:** Dependencies were merged into a single `packages/core/pyproject.toml` containing `playwright`, `fastapi`, `sqlalchemy`, and `rapidfuzz`. The package name was updated to `axiom-core`.

**Rationale:** A unified `core` package ensures all dependencies resolve correctly during installation in a single virtual environment without conflicts.
