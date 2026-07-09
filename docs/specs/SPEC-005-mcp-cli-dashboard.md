# SPEC-005: Operating Axiom — CLI, MCP, Dashboard

**Status:** Draft
**Implements:** [ADR-002 §6](../../ADR-002.md), [ADR-003 §5–6](../../ADR-003.md)
**LLD:** [LLD-008](../lld/LLD-008-mcp-server.md) (MCP + REST/WS), [LLD-009](../lld/LLD-009-cli.md) (CLI)

> The surfaces developers and coding agents use to drive Axiom. The **CLI** is the single process you
> start; it hosts the **MCP** control plane for agents and serves the **dashboard** for humans. Neither
> the CLI nor the dashboard ever executes tests — they call core.

---

## 1. Developer flow (CLI)

```
npx axiom init                 # scaffold .axiom/ + config in the project
npx axiom start                # spawn core (localhost), start MCP (stdio), open dashboard
npx axiom author "test the login flow" --entry https://app.local
                               # → spec.json (authored, for review)
npx axiom ground <testId>      # first live run → candidates.json + grounded test
npx axiom test [<testId>]      # deterministic run(s); prints RunReport; streams to dashboard
npx axiom heal <testId>        # maintenance heal for stale steps (LLM, explicit)
npx axiom stop
```

- `test` with no id runs the whole suite. Exit code reflects the verdict (CI-friendly).
- Everything the CLI does is a REST/WS call into core — the CLI holds no execution logic.

## 2. Coding-agent flow (MCP)

An agent connects to the MCP server (stdio) that `axiom start` hosts and drives Axiom with tools:

| Tool | Does | Backing |
|---|---|---|
| `getMap` | fetch the KDG / app-structure context for authoring | core `GET /kdg` |
| `getDelta` | diff of the KDG since a version (what changed) | core `GET /kdg/delta` |
| `healing` | fetch the repair payload `{ Spec IR, Test Case, KDG }` for a stale test | core `GET /tests/:id/repair` |
| `authorTest` / `submitSpec` | create/store a spec | core `POST /tests` |
| `runTest` | run a grounded test | core `POST /runs` |
| `getReport` / `pollRun` | fetch/poll a run report | core `GET /runs/:id` |
| `updateTest` (heal) | apply a maintenance repair | core `POST /tests/:id/maintain` |
| `deleteTest` | remove a test | core `DELETE /tests/:id` |

The agent **is** the authoring/maintenance LLM: it reads `getMap`, authors a spec, submits it, triggers
grounding, and for stale tests pulls `healing` context and submits a repair. No generative model runs
inside core's runtime.

## 3. Dashboard (thin this pass)

A minimal Vite+React SPA served by core; a developer tool, never an executor. It must answer two
questions — **is my test functional?** and **what does my suite cover?** — and show:

- **Results:** run history, pass/fail/stale per step, selection source (cached vs healed), timings.
- **Screenshots** of key test moments.
- **Selector map:** a structured view of the KDG / resolved elements (what Axiom "knows" about the app).
- **Coverage:** covered / total (methodology being researched — thin, future).
- **Suggested tests:** e.g. "you tested login; also test add-to-cart" (future).
- **Review queue:** stale steps with the failing snapshot + candidate list → trigger maintenance heal.
- **JSON test editor** (CodeMirror) with `shared` Zod validation for hand-edits.

Live run/log/screenshot updates stream over WebSocket into a plain auto-scrolling view (no terminal
emulator, no animation library). Detailed dashboard component design is out of scope here (deferred).

## 4. Boundaries (invariants)

- The **CLI never executes** tests (invariant #4) — it orchestrates and hosts MCP.
- The **dashboard never executes** tests (invariant #3) — it is a client of core's REST/WS.
- **MCP tools proxy to core over REST/WS** (invariant #7) — no internal cross-package calls.
- All business logic (authoring, grounding, resolving, running, healing) is in **core** (invariant #6).
