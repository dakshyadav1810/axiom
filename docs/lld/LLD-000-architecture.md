# LLD-000: Architecture — Monorepo, Packages, Process Model

**Status:** Draft
**Implements:** [ADR-003](../adr/ADR-003.md), [PLAN-001](../PLAN-001.md)
**See also:** [SPEC-000](../specs/SPEC-000-overview.md), [LLD-001](./LLD-001-shared-ir.md)

> The top-level implementation map: what the packages are, how they depend on each other, what runs in
> which process, and how data flows through the system. Every other LLD slots into this.

---

## 1. Stack

- **Language/runtime:** TypeScript 5.x (strict, ESM) on **Node.js LTS 22+**. No Python, no Bun.
- **Monorepo:** **pnpm workspaces** + **Turborepo** (build/test caching).
- **Build:** **tsup** (esbuild) for libraries/CLI; **Vite** for the dashboard.
- **Test:** **Vitest** (unit + golden cases). **Lint/format:** **Biome**.
- **Install/run:** `npx axiom` — one command, no toolchain setup.

## 2. Packages & dependency direction

```
          ┌─────────────────────────────────────────────┐
          │                packages/shared               │  Zod IR — no runtime deps on siblings
          │   spec · candidates · resolver · config ·    │
          │            REST DTOs · WS messages           │
          └───────▲──────────────▲───────────────▲───────┘
                  │              │               │
        imports   │      imports │       imports │
     ┌────────────┴───┐  ┌───────┴────────┐  ┌───┴──────────────┐
     │  packages/cli  │  │  packages/core │  │ packages/dashboard│
     │  commander +   │  │  Fastify — ALL │  │  Vite+React SPA   │
     │  MCP (stdio)   │  │  business logic│  │  → builds into    │
     │                │──▶│  REST + WS     │◀─│  core/static      │
     └────────────────┘  └────────────────┘  └───────────────────┘
        proxies MCP→REST     owns execution      client only
```

**Rules (invariants #6/#7/#8):**
- `shared` depends on nothing internal; everyone imports it. It is the *only* place a schema is defined.
- `core` owns all business logic. `cli` and `dashboard` reach it **only** over REST/WebSocket.
- `cli` contains no execution logic; its MCP tools translate to REST/WS calls into `core`.
- `dashboard` is a pure client, built to static assets served by `core`.
- Each subsystem inside `core` sits behind an interface (so the resolver, cache, adapters are replaceable).

## 3. `packages/core` internal layout (feature-domain)

```
packages/core/src/
├── server/        # Fastify app: REST routes, @fastify/websocket, @fastify/static (dashboard),
│                  #   fastify-type-provider-zod (validate at the edge with shared schemas)
├── authoring/     # MCP-mediated authoring: KDG context provider, spec validate + store   → LLD-002
├── grounding/     # first live run: DOM extract, candidate build, band gate, normalize     → LLD-003
├── resolver/      # 5 signal strategies + MoE router + banding (pure, no I/O)               → LLD-004
├── execution/     # Step Dispatcher → UI/API/DB adapters; assertion engine; verdicts        → LLD-005
├── healing/       # runtime re-ground loop + maintenance repair-payload builder             → LLD-006
├── recording/     # Playwright recorder; typed in-page modules (former page.evaluate)       → LLD-005
├── cache/         # Drizzle + better-sqlite3: resolution/selector + embedding cache          → LLD-007
├── storage/       # artifact store (JSON-in-git) reader/writer                               → LLD-007
├── kdg/           # knowledge graph interface + contents contract (data structure deferred)  [thin]
└── (network/, benchmarks/)                                                                   [thin]
```

Only `authoring/` ever reaches a generative LLM, and it does so **through MCP**, at authoring/maintenance
time — never during a run. Everything below `authoring/` is deterministic.

## 4. Process & runtime model

`npx axiom start` launches **one CLI process** that:
1. spawns + health-checks the **core** Fastify server (localhost) via `execa`;
2. starts the **MCP server** (stdio) in-process (CLI), whose tools call core over REST/WS;
3. serves the **dashboard** (static assets bundled into `core/static`) at the core base path and opens it.

```
 developer ──▶ npx axiom ──┬─▶ CLI process ──spawn──▶ core (Fastify, :PORT)
 coding agent ─(stdio MCP)─┘        │                      │  Playwright
                                    └── MCP tools ──REST/WS─┘  SQLite cache
                                                              serves dashboard SPA
```

There is no separate backend to deploy and no Python venv. `npx axiom test` runs the committed grounded
tests deterministically from cache; it needs only Node + a browser.

## 5. End-to-end data flow (maps to the LLDs)

```
intent ─▶ authoring(LLM via MCP) ─▶ spec.json ─▶ grounding(Playwright live run) ─▶ candidates.json
                                                        │
                                              normalize (shared schema)
                                                        │
                                                   resolver ─▶ resolution (winner + band)
                                                        │
                                    grounded test (+cachedSelector) ──▶ git (versioned)
                                                        │                     │
                                                        └────────── run ──────┴── SQLite cache (regenerable)
                                                                     │
                                              cached selector → resolver-heal → stale
                                                                     │
                                                            act → assert → verdict
```

## 6. Tooling & conventions

- **Config:** `node --env-file`; typed config validated against a `shared` Zod schema.
- **Errors/logging:** `pino` structured logs in core; typed error unions surfaced over REST/WS.
- **Auth:** `jose` (JWT) — dev-mode bypass locally; real tokens for the paid/cloud tier.
- **Testing:** Vitest everywhere; the resolver ships **golden-case tests** that lock the tuned behavior
  documented in [DISCUSSION.md](../DISCUSSION.md) (see LLD-004).
- **Naming:** kebab-case files, PascalCase types, camelCase members; each subsystem exports a small
  interface + a default implementation.

## 7. Invariant mapping

| Invariant | Where enforced |
|---|---|
| Core owns execution | all of `core/execution`, `core/resolver` (LLD-004/005) |
| Tests stored as JSON | `storage/` artifacts (LLD-007); Playwright scripts never persisted |
| Dashboard/CLI never execute | `cli` = orchestration+MCP (LLD-009); `dashboard` = client (SPEC-005) |
| Resolver deterministic-first | `resolver/` — local embeddings, no runtime LLM (LLD-004) |
| REST/WS-only comms | `server/` is the only ingress; MCP proxies to it (LLD-008) |
| Subsystems behind interfaces | each `core/*` module exports an interface |

## 8. Reference (retired Python core)

The existing `packages/core/**/*.py` (~21.6k LOC) is an **executable reference spec** during the rewrite:
the resolver ladder, executor behavior, and DOM-extraction logic are read to re-earn parity (locked by
Vitest golden cases), then the Python tree is deleted. It is never imported or shipped.
