# PLAN-001: Axiom Tech Stack — All-TypeScript, Bundled Dashboard, MCP-in-CLI

**Status:** Proposed
**Date:** 2026-07-10
**Author:** Shubham Krishan
**Relationship:** Implements the stack for ADR-001 (deterministic runtime) and ADR-002 (spec/grounding/MCP pipeline).

## Context

Axiom is an intent-driven, **deterministic-first** testing platform. The ADRs fix the
architecture: LLMs author only, runtime is deterministic (ADR-001); intent compiles through
`spec.json → grounding → candidates.json → normalize → resolver → SQLite cache → Playwright`
with an MCP server as the agent-facing control plane (ADR-002).

Today the repo is three languages: **CLI** = Bun/TS (a stub), **core** = ~21.6k lines of Python
(FastAPI/uvicorn/Playwright/Pydantic/aiosqlite/supabase/rapidfuzz), **dashboard** = Next.js 16 SPA
as a separate deployable package.

**Decisions made in this planning session:**

1. **Go all-TypeScript on one runtime (Node), ditching Python entirely.** The usual reason to keep
   Python — scientific/ML coupling — does not apply: the only pythonic dependency across 21.6k lines
   is `rapidfuzz` in one file, and ADR-001 keeps all LLM/semantic work at authoring time via API
   calls, not local models. Meanwhile the TS case is unusually strong for *this* project: Playwright
   is natively Node (Python binds to it over a driver subprocess); 34 `page.evaluate` sites mean the
   recorder/resolver already lives partly in JS; the whole system is IR/artifact-driven, so schemas
   defined **once in Zod** are shared across every package instead of Pydantic-vs-Zod drift.
2. **Build from scratch** (not incremental) — treat the Python core as an executable spec/reference,
   not code to preserve. The project is pre-1.0 (CLI stub, dashboard scaffolded, ADRs in flight,
   band thresholds untuned), so paying the rewrite cost now beats a permanent two-language tax.
3. **Bundle the dashboard inside the core server** — it is "only a client," built to static assets
   and served by the TS server; no separate deployable.
4. **CLI is the Node orchestration + MCP comms layer** between developer/agent and the core.

Intended outcome: one language, one runtime, one `npx axiom` install (no Python venv/uv), and a
single shared IR contract end-to-end.

---

## Recommended Stack

### Monorepo (root)

- **Node.js LTS (22+)**, **TypeScript 5.x** — strict, ESM everywhere.
- **pnpm workspaces** + **Turborepo** for build/test orchestration and caching.
- **tsup** (esbuild) for library/CLI builds; **Vitest** for tests; **Biome** for lint+format (single fast tool).

### `packages/shared` (NEW — the payoff of single-language)

- **Zod** schemas + inferred TS types for the Spec IR (`spec.json` step + Tier-1 target),
  `candidates.json`, resolver models, config, REST DTOs, and WS message shapes.
- Replaces Pydantic; consumed by core, cli, and dashboard so the IR has exactly one definition.

### `packages/core` (TS server — owns all business logic)

- **Fastify** + **@fastify/websocket** (execution/recording/resolver event streams) +
  **@fastify/static** (serves the bundled dashboard) + **fastify-type-provider-zod** (validate at the edge with shared schemas).
- **Playwright** (native Node) — recorder + execution adapter; move `page.evaluate` strings into typed, testable in-page modules.
- **better-sqlite3** behind a **Drizzle ORM** schema for the ephemeral resolution/selector cache **and cached embeddings** (SQLite per ADR-002).
- **Semantic resolver = true semantic search**, not fuzzy matching. Use a **local embedding model** (**transformers.js** `@huggingface/transformers`, or **fastembed-js** — ONNX, small model e.g. `all-MiniLM-L6-v2`/`bge-small`, runs in-process) + in-process **cosine similarity** over the candidate set; embeddings cached in SQLite. `rapidfuzz`/`fuzzball` and all fuzzy-string matching are **removed** — fuzzy was a prior workaround, semantic search is the intended signal. The model has fixed offline weights and makes no generative/API call, so runtime stays **deterministic and LLM-free** per ADR-001.
- **jose** (JWT, replaces PyJWT), **@supabase/supabase-js** (paid/cloud tier), **pino** logging, `node --env-file` for config.
- Feature-based layout: `resolver/`, `recording/`, `execution/`, `grounding/`, `network/`, `benchmarks/`, `server/`, `cache/` — each behind an interface (invariant #8).

### `packages/cli` (Node orchestration + MCP)

- CLI framework: **commander**. Commands: `init`, `start`, `stop`, `author`, `ground`, `test`, `heal`, `report` (LLD-009 §2). `start` writes `.axiom/axiom.pid`; `stop` reads it to SIGTERM core.
- **@modelcontextprotocol/sdk** (official TS, stdio transport) — the agent-facing MCP server started by
  `axiom start`, exposing `getMap`, `getDelta`, `healing`, and test CRUD (run/report/poll/update/delete).
- Orchestration via `node:child_process`/**execa**: spawn + health-check the core server, open the dashboard (`open`).
- **MCP tools translate to REST/WS calls into core** — never internal cross-package calls (invariant #7). The CLI contains no execution logic (invariant #4).

### `packages/dashboard` (bare-minimum Vite SPA, served directly from core)

- **Vite + React 19 + TypeScript + Tailwind 4** only. Built to static assets in `packages/core/static/` and served by Fastify at one base path — no separate server, no separate deploy. **Deliberately minimal; do not overengineer.**
- **TanStack Query** (REST) + the native **WebSocket** API for live streams. Log/progress streaming is a plain auto-scrolling component — **no xterm, no terminal emulator, no framer-motion**.
- **CodeMirror 6** for JSON test editing (lighter than Monaco; drop `@monaco-editor/react`), Zod schemas imported from `packages/shared` for validation.
- Small `useState`/Context or **zustand** for local state; **recharts** only if/when benchmark viz lands. Routing: **React Router** if more than a couple of views are needed. Client only — never executes tests (invariant #3).

### Communication (unchanged from AGENTS.md, retargeted)

- Dashboard ↔ core: REST (history/config/projects/tests/analytics) + WebSocket (execution/logs/screenshots/resolver/benchmark).
- Agent/developer ↔ core: MCP (stdio, via CLI) → proxied to REST/WS.

---

## How the stack satisfies the ADRs

- **ADR-001 (deterministic runtime):** resolver + execution adapter are pure TS, LLM-free. The semantic signal uses a **fixed local embedding model** (deterministic vectors, no generative/network call), not a runtime LLM. Generative LLM use stays at authoring, reached through MCP.
- **ADR-002 (pipeline):** `spec.json` = Zod IR (DOM-blind) → Grounding (Playwright live run → `candidates.json`, `band ≥ medium` gate, else `ungrounded`) → Normalize (shared schema) → resolver → **SQLite (Drizzle) cache** → Playwright execution (cached → resolver-heal → stale). Versioned JSON artifacts in git; SQLite holds only regenerable cache. MCP control plane in the CLI.

---

## Build Order (from scratch)

1. **Scaffold monorepo**: pnpm workspaces, Turborepo, base tsconfig, Biome, Vitest; create the 4 packages.
2. **`shared`**: author the Zod Spec IR (step + Tier-1 target), candidates, resolver models, config, DTOs, WS messages. *(ADR-002 action #1)*
3. **`core` skeleton**: Fastify app, config, Drizzle/SQLite cache layer, static mount, pino, health check.
4. **Recording**: Playwright recorder → spec/flow JSON; port `page.evaluate` logic to typed in-page modules.
5. **Resolver**: signal strategies (semantic via local-embedding cosine search; affordance as a **gate**, not a weighted signal; context, structure, index) + router with base weights `semantics 0.45 · context 0.33 · structure 0.22` — deterministic. Wire the embedding model + SQLite embedding cache. Golden-case tests port the tuned behavior documented in `DISCUSSION.md`.
6. **Grounding + Normalize + resolve + cache** with the `band ≥ medium` accept gate; grounded test stores the **winner only**, full ranking to `candidates.json`. *(ADR-002 #2–3)*
7. **Execution adapter**: locate ladder = **selector cache (by domHash) → grounded-artifact selector → resolver-heal → stale**; runtime algorithmic heal loop, owned by the healing service, persists heals to cache (never the versioned artifact). *(ADR-002 #4–5)*
8. **REST + WS surface**: recording, steps, projects, flows, test run/report, live streams.
9. **`cli`**: commander commands + spawn/health-check core + MCP server (`getMap`/`getDelta`/`healing` + CRUD) proxied to REST/WS. *(ADR-002 #6–7)*
10. **`dashboard`**: bare-minimum Vite SPA → build into `core/static`; wire REST + native WS; JSON test editor (CodeMirror), simple live-run/log view (plain auto-scroll component). Add charts only if benchmark viz is in scope.
11. **Maintenance heal** flow with the `{ Spec IR, Test Case, KDG }` repair payload. *(ADR-002 #6)*
12. **Docs**: rewrite AGENTS.md package table (Bun→Node/TS, Python→TS, dashboard now bundled), log the shift in DECISIONS.md, and add **ADR-003** recording the all-TypeScript + bundled-dashboard + MCP-in-CLI decision.

## Critical files / entry points

- `packages/shared/src/schema/*.ts` — the single IR definition.
- `packages/core/src/server/app.ts` (Fastify), `packages/core/src/resolver/router.ts`, `packages/core/src/cache/` (Drizzle/SQLite), `packages/core/static/` (dashboard build output).
- `packages/cli/src/index.ts` (commander) + `packages/cli/src/mcp/server.ts` (@modelcontextprotocol/sdk).
- `packages/dashboard/vite.config.ts` (outDir → `../core/static`).
- Reference-only during rewrite: the existing `packages/core/**/*.py` (resolver ladder, executor, recorder).

## Verification

- `pnpm -w build && pnpm -w test` (Turborepo) — Vitest resolver golden cases confirm signal parity with the Python behavior.
- `npx axiom start`: one Node process spawns the Fastify core (localhost), brings up the MCP server (stdio), and serves the dashboard at the core base path.
- Author a spec via an MCP `healing`/CRUD tool → run Grounding against a live page → assert `candidates.json` + `cachedSelector` written and `band ≥ medium` (else `ungrounded`).
- `npx axiom test` runs deterministically from cache; break a selector to trigger the runtime heal → `stale` path.
- Open the dashboard: edit a JSON test in CodeMirror and watch a live run stream over WebSocket in the plain log view.
- Connect an agent to the MCP server and exercise `getMap` / `getDelta` / `healing` + test CRUD.
