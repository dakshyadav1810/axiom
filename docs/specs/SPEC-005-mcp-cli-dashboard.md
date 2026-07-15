# SPEC-005: Operating Axiom — CLI, MCP, Dashboard

**Status:** Draft
**Implements:** [ADR-002 §6](../adr/ADR-002.md), [ADR-003 §5–6](../adr/ADR-003.md)
**LLD:** [LLD-008](../lld/LLD-008-mcp-server.md) (MCP + REST/WS), [LLD-009](../lld/LLD-009-cli.md) (CLI)

> The surfaces developers and coding agents use to drive Axiom. The **CLI** is the single process you
> start; it hosts the **MCP** control plane for agents and **opens** the **dashboard** for humans (the
> dashboard's static assets are served by **core**, not the CLI). Neither the CLI nor the dashboard ever
> executes tests — they call core.

---

## 1. Developer flow (CLI)

```
npx axiom init                 # scaffold .axiom/ + config in the project
npx axiom start                # spawn core (localhost), write .axiom/axiom.pid, start MCP (stdio), open dashboard
npx axiom ground <testId>      # first live run → candidates.json + grounded test
npx axiom test [<testId>]      # deterministic run(s); prints RunReport; streams to dashboard
npx axiom heal <testId>        # print the repair payload for a stale test (no LLM call — read-only)
npx axiom stop                 # read .axiom/axiom.pid → SIGTERM the core process, remove the pidfile
```

- **There is no `axiom author` command.** Axiom holds no LLM client — a spec can only be created by a
  connected agent calling `submitSpec` over MCP (SPEC-001 §2). `axiom heal` is read-only for the same
  reason: it prints the repair payload so you can hand it to your agent; it doesn't attempt a fix itself.
- `test` with no id runs the whole suite. Exit code reflects the verdict (CI-friendly).
- `start` runs core as a child process and records its PID in `.axiom/axiom.pid`; `stop` (from any
  terminal) reads that pidfile to shut core down. Foreground `start` also stops on Ctrl-C.
- Everything the CLI does is a REST/WS call into core — the CLI holds no execution logic.

## 2. Coding-agent flow (MCP)

An agent connects to the MCP server (stdio) that `axiom start` hosts and drives Axiom with tools:

| Tool | Does | Backing |
|---|---|---|
| `getMap` | fetch the KDG / app-structure context for authoring | core `GET /kdg` |
| `getDelta` *(future — needs KDG versioning)* | diff of the KDG since a version | core `GET /kdg/delta` |
| `healing` | fetch the repair payload `{ Spec IR, Test Case, KDG }` for a stale test | core `GET /tests/:id/repair` |
| `submitSpec` | store an agent-authored spec (validate + lint) | core `POST /tests` |
| `runTest` | run a grounded test | core `POST /runs` |
| `getReport` (alias `pollRun`) | fetch/poll a run report | core `GET /runs/:id` |
| `updateTest` (heal) | apply a maintenance repair — `spec` is **required**, the agent always supplies it | core `POST /tests/:id/maintain` |
| `deleteTest` | remove a test | core `DELETE /tests/:id` |

**The agent is the only authoring/maintenance LLM — Axiom has none of its own.** It reads `getMap`,
authors the spec using its own model, submits it via `submitSpec`, triggers grounding, and for stale
tests pulls `healing` context and submits the fix via `updateTest`. There is no `authorTest` tool and no
code path where core calls out to a model provider — not at runtime, and not at authoring time either.

## 3. Dashboard (thin this pass)

A minimal Vite+React SPA served by core; a developer tool, never an executor. It must answer two
questions — **is my test functional?** and **what does my suite cover?** — and show:

- **Results:** run history, pass/fail/stale per step, selection source (cached vs healed), timings.
- **Screenshots** of key test moments.
- **Selector map** *(future — KDG-dependent):* a structured view of the KDG / resolved elements (what
  Axiom "knows" about the app). Ships once the KDG data structure is defined; until then the dashboard
  shows resolved elements per grounded test only.
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
