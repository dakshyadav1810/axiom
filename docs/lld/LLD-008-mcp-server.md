# LLD-008: MCP Server + Core REST/WS Surface

**Status:** Draft
**Implements:** [SPEC-005](../specs/SPEC-005-mcp-cli-dashboard.md), [ADR-002 §6](../../ADR-002.md), [ADR-003 §6](../../ADR-003.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md) (DTOs/WS), [LLD-009](./LLD-009-cli.md) (host)

> The agent-facing **MCP server** lives in the **CLI** and is a thin proxy: every tool translates to a
> REST/WebSocket call into **core**. Core's Fastify surface is the single ingress for all business logic.
> This preserves invariant #7 (no internal cross-package calls) while giving `axiom start` an MCP control
> plane.

---

## 1. Topology

```
 coding agent ──stdio(MCP)──▶ CLI: mcp/server.ts ──HTTP/WS──▶ core: Fastify (REST + WS)
                              (@modelcontextprotocol/sdk)        (fastify-type-provider-zod)
```

- MCP transport: **stdio** (`@modelcontextprotocol/sdk`, official TS). Started by `axiom start`.
- Each MCP tool handler builds a typed request from `shared` DTOs and calls core over `http://127.0.0.1:PORT`.
- Tools never touch Playwright, the DB, or the resolver directly — only core's REST/WS.

## 2. MCP tool contracts (CLI `mcp/server.ts`)

| Tool | Input (Zod, from `shared`) | Proxies to | Returns |
|---|---|---|---|
| `getMap` | `{ entryUrl }` | `GET /kdg?entry=` | `KdgContext` |
| `getDelta` | `{ sinceVersion }` | `GET /kdg/delta?since=` | KDG diff |
| `authorTest` | `AuthorRequest` | `POST /tests` (author) | `{ testId, spec }` |
| `submitSpec` | `SpecIR` | `POST /tests` (submit) | `{ testId }` |
| `groundTest` | `{ testId }` | `POST /tests/:id/ground` | `GroundingOutcome` summary |
| `runTest` | `RunRequest` | `POST /runs` | `{ runId }` |
| `pollRun` / `getReport` | `{ runId }` | `GET /runs/:id` | `RunReport` |
| `healing` | `{ testId }` | `GET /tests/:id/repair` | `RepairPayload` |
| `updateTest` | `{ testId, stepIds }` | `POST /tests/:id/maintain` | `RepairResult` diff |
| `deleteTest` | `{ testId }` | `DELETE /tests/:id` | `{ ok }` |

Tool schemas are the `shared` Zod types → JSON Schema, so the agent sees exact contracts.

## 3. Core REST endpoints (Fastify, validated with `fastify-type-provider-zod`)

| Method + path | Body / query | Response | Owner LLD |
|---|---|---|---|
| `POST /tests` | `AuthorRequest` \| `SpecIR` | `SpecIR` + `testId` | LLD-002 |
| `POST /tests/:id/ground` | — | `GroundingOutcome` | LLD-003 |
| `POST /tests/:id/maintain` | `{ stepIds }` | `RepairResult` | LLD-006 |
| `GET /tests/:id/repair` | — | `RepairPayload` | LLD-006 |
| `GET /tests` / `GET /tests/:id` | — | summaries / `GroundedTest` | LLD-007 |
| `DELETE /tests/:id` | — | `{ ok }` | LLD-007 |
| `POST /runs` | `RunRequest` | `{ runId }` (async) | LLD-005 |
| `GET /runs/:id` | — | `RunReport` | LLD-005/007 |
| `GET /kdg` / `GET /kdg/delta` | `entry` / `since` | `KdgContext` / diff | LLD-002 (kdg) |
| `GET /health` | — | `{ ok, version }` | LLD-000 |

Every request/response is validated at the edge against the `shared` schema; validation failure returns a
typed 4xx.

## 4. WebSocket surface (`@fastify/websocket`)

- `GET /ws/runs/:id` — streams `WsMessage` (LLD-001 §7): `run.start`, `step.start`, `resolver.event`,
  `step.result`, `log`, `run.complete`.
- `GET /ws/ground/:id` — streams grounding progress (per-step candidate/band events) for the dashboard.

The dashboard and (optionally) the MCP `pollRun` consume these; messages are the same `shared` union, so
there is one wire contract.

## 5. Auth

- Local dev: a dev-mode bypass (loopback only).
- Cloud/paid tier: **jose** JWT verification on REST/WS; the CLI forwards the token it holds. Core is the
  only tier that validates (invariant #6). MCP inherits the CLI's session.

## 6. Error model

Uniform typed errors over REST/WS: `{ error: { code, message, details? } }` with codes for
`validation`, `not_found`, `ungrounded`, `stale`, `provider_error` (authoring), `browser_error`. MCP maps
these to tool errors so the agent gets structured failures.

## 7. Boundaries

- The MCP server is **stateless** — all state lives in core (invariant #6). Restarting the agent/MCP loses
  nothing.
- No tool bypasses REST/WS; there is no in-process shortcut into core (invariant #7).
