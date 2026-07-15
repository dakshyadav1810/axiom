# Architectural Decisions Log

This document tracks specific engineering decisions made on the Axiom project.

> **⚠️ Entries 1–4 are historical and superseded by [ADR-003](adr/ADR-003.md).** They describe decisions made
> inside the retired **Python** core (FastAPI/SQLAlchemy/Pydantic/rapidfuzz). Axiom is now a single-language
> **TypeScript on Node** project; the Python tree is a reference-only executable spec, deleted once parity
> is verified. Read entries 1–4 for motivation only — their file paths and technologies no longer exist.
> Current decisions start at entry 5.

## 1. Split Monolithic Recorder into Feature Domains (2026-07-04) — *superseded by ADR-003*

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

---

## 5. Single-Language TypeScript Stack (2026-07-10)

**Context:** The three-language split (Bun/TS CLI, ~21.6k-line Python core, separate Next.js dashboard) imposed a permanent schema-duplication and Playwright-subprocess tax on a pre-1.0, IR-driven project.

**Decision:** Rebuild as one TypeScript-on-Node monorepo (`shared` Zod IR, `core` Fastify, `cli` commander+MCP, `dashboard` Vite SPA bundled into core). Fuzzy matching (`rapidfuzz`) is replaced by a local fixed-weight ONNX embedding model + cosine similarity. Full rationale and alternatives in [ADR-003](adr/ADR-003.md); build order in [PLAN-001](PLAN-001.md). Supersedes entries 1–4.

**Rationale:** One language, one runtime, one shared IR eliminates Pydantic↔Zod drift; Playwright runs natively; `npx axiom` is the only install step.

## 6. Runtime Locate Ladder is Cache-First (2026-07-15)

**Context:** The LLDs disagreed on where the runtime fast-path selector is read from — the `resolution_cache` table (LLD-007) vs. the grounded artifact (LLD-005) — leaving healed selectors written to a cache nothing consulted and the same step re-healing every run.

**Decision:** The locate ladder is **selector cache (keyed by `(testId, stepId, domHash)`) → grounded-artifact selector → runtime heal → stale**. The SQLite cache is the fast path; the versioned artifact is the durable seed used when the cache is cold or the page changed. A confident runtime heal writes to the cache (never the versioned artifact), so the next run on the changed page hits cache. See LLD-005 §4, LLD-006 §3, LLD-007 §4.

**Rationale:** Preserves the "deleting `cache.db` loses only speed" invariant while making heals actually stick, and keeps runtime writes off the git-versioned artifacts.

## 7. Affordance is a Gate, Not a Weighted Signal (2026-07-15)

**Context:** LLD-004 both hard-filtered candidates on affordance *and* gave affordance weight 0.1 as a 0/1 value. Every surviving candidate scored 1, adding a constant offset that silently skewed scores against the absolute band thresholds.

**Decision:** Affordance is purely the pre-scoring gate. The weighted signals are `semantics 0.45 · context 0.33 · structure 0.22` (sum 1.0); index remains a tiebreak, unweighted. See LLD-004 §5.

**Rationale:** A constant contributor carries no discriminative value and only distorts banding; removing it makes the final score a clean blend of the informative signals.

## 8. Grounded Test Stores the Winner Only (2026-07-15)

**Context:** The grounded artifact embedded the full ranked candidate list, duplicating `candidates.json` and putting volatile per-candidate DOM data into the durable, git-versioned tier — the very churn ADR-002 rejected `flow.json` for.

**Decision:** The versioned grounded test stores a **winner-only** resolution (selected candidate + anchors); the full ranking stays in `candidates.json`. `GroundedTarget.resolution` is optional so partially grounded tests (halted at the first ungrounded step) validate. See LLD-001 §6.

**Rationale:** Keeps the durable artifact small and stable across UI reshuffles; a partial grounding pass must still round-trip through the schema for review.

## 9. Maintenance Heal Entry Point; Negative-Test Flag in the IR (2026-07-15) — *`patchedSpec?` superseded by entry 10*

**Context:** SPEC-005 had the agent author repairs while the `updateTest` tool had nowhere to put a repaired spec, and LLD-006 called an undefined `llmRepair()`. Separately, negative tests were specced (verdict inversion) but had no representable field in the IR.

**Decision:** (a) `maintain(testId, stepIds, patchedSpec?)` — agent path passes the patched `SpecIR` via `updateTest`/`POST /tests/:id/maintain`; CLI path omits it and core calls a provider through `AuthoringService.repair()`. **This CLI/provider branch was removed the same day — see entry 10.** (b) Add `negative: boolean` to the step schema; the assertion engine inverts the verdict when set. This part stands. See LLD-006 §6, LLD-002, LLD-008, LLD-001 §3, SPEC-003 §6, SPEC-004 §4.

**Rationale:** Specced behavior must have a home in the schema (the negative-test half of this decision). The maintenance-heal half was corrected almost immediately — see entry 10 for why.

## 10. Axiom Never Calls an LLM Provider — Authoring Is Agent-Only (2026-07-15)

**Context:** Entry 9 (and, before it, `SPEC-001`/`LLD-002`/`LLD-008`/`LLD-009` as originally drafted) described **two** authoring/maintenance paths: an "agent path" where a connected coding agent authors the spec and calls `submitSpec`/`updateTest`, and a "CLI/provider path" where a bare `axiom author "<intent>"` invocation had core call a configured LLM provider (Anthropic/OpenAI) directly, holding an API key in `AxiomConfig.llm` and billing the developer's own provider account per call. This was built and briefly shipped (`AnthropicLlmClient`, `packages/core/src/authoring/llm-client.ts`, `AXIOM_LLM_API_KEY`) before being caught as a misread of the original intent: **Axiom was never meant to hold a provider client at all.** The only intended authoring mechanism is the developer's own already-running coding agent (Claude Code, Cursor, ...), interacting with Axiom exclusively through MCP.

**Decision:** Remove the CLI/provider path entirely. `AuthoringService` now has one way to create a spec — `submit(spec)` — which validates and stores a spec the caller (always an agent) already authored. `HealingService.maintain(testId, stepIds, patchedSpec)` now requires `patchedSpec`; there is no core-side fallback that generates one. `AxiomConfig` has no `llm` block and no API key anywhere. The `authorTest` MCP tool and `axiom author` CLI command are removed; `axiom heal` becomes read-only (prints the repair payload instead of attempting a repair). See `SPEC-001` §2, `LLD-002`, `LLD-006` §6, `LLD-008` §2–3, `LLD-009` §2.

**Rationale:** The product's entire value proposition is that intelligence lives in authoring and nowhere else runtime-adjacent (ADR-001) — but *whose* intelligence was never meant to be Axiom's own provider bill. The developer already has an LLM session open to talk to Axiom in the first place; giving Axiom a second, independent path to call a model directly duplicates cost, duplicates the trust boundary (a second API key to secure), and contradicts the "no vendor lock-in, nothing leaves your machine unless you already sent it somewhere" positioning. One entry point, held to one already-trusted actor, is simpler and is what was actually intended.
