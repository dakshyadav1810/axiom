# LLD-009: CLI Orchestrator (`packages/cli`)

**Status:** Draft
**Implements:** [SPEC-005](../specs/SPEC-005-mcp-cli-dashboard.md), [ADR-003 §6](../adr/ADR-003.md), [PLAN-001](../PLAN-001.md)
**Depends on:** [LLD-008](./LLD-008-mcp-server.md) (MCP host), [LLD-001](./LLD-001-shared-ir.md) (config/DTOs)

> `npx axiom` — the single process a developer or agent starts. It orchestrates lifecycle (spawn + health
> the core server, open the dashboard) and hosts the MCP control plane. It contains **no execution logic**
> (invariants #4/#6): every command is a REST/WS call into core.

---

## 1. Module shape

```
packages/cli/src/
├── index.ts            # commander program (entry: bin "axiom")
├── commands/           # init | start | stop | ground | test | heal | report
├── core-process.ts     # spawn + health-check + shutdown the core server (execa)
├── client.ts           # typed REST/WS client for core (uses shared DTOs)
├── mcp/server.ts       # @modelcontextprotocol/sdk stdio server (LLD-008)
└── config.ts           # load + validate AxiomConfig (node --env-file)
```

## 2. Command surface (commander)

| Command | Does | Calls |
|---|---|---|
| `axiom init` | scaffold `.axiom/` + `axiom.config.json` | local FS |
| `axiom start` | spawn core, start MCP (stdio), serve+open dashboard | `core-process` + `mcp/server` |
| `axiom stop` | graceful shutdown of core | `core-process` |
| `axiom ground <testId>` | first-run grounding | `POST /tests/:id/ground` |
| `axiom test [<testId>]` | run test / suite; print report; stream to dashboard | `POST /runs` + `GET /ws/runs/:id` |
| `axiom heal <testId>` | print the repair payload for a stale test | `GET /tests/:id/repair` |
| `axiom report <runId>` | print a stored run report | `GET /runs/:id` |

`axiom test` sets the process exit code from the run verdict (0 pass / non-zero fail) for CI use.

**There is no `axiom author` command.** Axiom has no LLM client of its own, so there is nothing a bare CLI
invocation could call to generate a spec — authoring only happens through a connected agent's `submitSpec`
MCP call (SPEC-001 §2). `axiom heal` is read-only for the same reason: it fetches and prints the repair
payload (`{ specIR, testCase, kdg }`) so the developer can hand it to their agent; it does not attempt a
repair itself.

## 3. Lifecycle (`core-process.ts`, `execa`)

```ts
async start() {
  const proc = execa("node", [coreEntry], { env: { ...process.env, AXIOM_PORT } });
  await waitForHealth(`http://127.0.0.1:${AXIOM_PORT}/health`, { timeoutMs: 15000 });
  await mcp.start();                 // stdio MCP server, proxying to core
  await open(`http://127.0.0.1:${AXIOM_PORT}/`);   // dashboard served by core
  registerShutdown(() => proc.kill("SIGTERM"));
}
```

- Core is a child process; the CLI supervises it (health poll, restart-on-crash optional, clean SIGTERM).
- In `start`, MCP and dashboard come up only after `/health` passes.
- The dashboard is **served by core** (static assets); the CLI only opens the URL.

## 4. Core client (`client.ts`)

A thin typed wrapper over `fetch`/`undici` + `WebSocket`, using the `shared` DTOs so requests/responses
are validated on the CLI side too. This is the *only* way the CLI talks to core — there is no direct
import of core internals (invariant #7).

## 5. MCP host (`mcp/server.ts`)

Starts the stdio MCP server (LLD-008) and registers the tool set. Each tool handler uses `client.ts` to
call core; tool schemas are the `shared` Zod types. The MCP server shares the CLI's config/session (auth
token, base URL) but holds no state of its own.

## 6. Config (`config.ts`)

`AxiomConfig` (LLD-001 §7) is loaded via `node --env-file` + `axiom.config.json`, validated with Zod, and
passed to the spawned core via env. Precedence: CLI flags → env → `axiom.config.json` → defaults.

## 7. Boundaries

- No Playwright, no resolver, no DB in the CLI (invariant #4).
- The CLI is disposable: killing it stops orchestration; core + artifacts persist independently.
- Distributed as an `npx`-runnable bin; `npx axiom` is the only install step (ADR-003).
