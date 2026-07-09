# Axiom Design Docs

Implementation-facing design for Axiom, derived from the ADRs. **Specs** describe business logic and user
flows; **LLDs** describe implementation and code detail. Design is clean-room from the ADRs — the retired
Python `packages/core` is reference only.

## Read in this order

1. **[SPEC-000 — Overview & Glossary](specs/SPEC-000-overview.md)** — start here; vocabulary + doc map.
2. **[LLD-000 — Architecture](lld/LLD-000-architecture.md)** — monorepo, packages, process model.
3. **[LLD-001 — Shared IR](lld/LLD-001-shared-ir.md)** — the Zod schemas everything else uses.

Then by pipeline stage (each SPEC pairs with its LLD):

| Stage | Spec (business logic + flow) | LLD (implementation) |
|---|---|---|
| Authoring | [SPEC-001](specs/SPEC-001-authoring.md) | [LLD-002](lld/LLD-002-authoring.md) |
| Grounding | [SPEC-002](specs/SPEC-002-grounding.md) | [LLD-003](lld/LLD-003-grounding+normalize.md) |
| Resolver | (within SPEC-002/003) | [LLD-004](lld/LLD-004-resolver.md) |
| Execution + Assertions | [SPEC-003](specs/SPEC-003-execution+assert.md) | [LLD-005](lld/LLD-005-execution.md) |
| Healing | [SPEC-004](specs/SPEC-004-healing.md) | [LLD-006](lld/LLD-006-healing.md) |
| Storage | (within SPEC-002/003) | [LLD-007](lld/LLD-007-storage.md) |
| CLI / MCP / Dashboard | [SPEC-005](specs/SPEC-005-mcp-cli-dashboard.md) | [LLD-008](lld/LLD-008-mcp-server.md), [LLD-009](lld/LLD-009-cli.md) |

## Decisions these docs implement

- **[ADR-001](../ADR-001.md)** — LLM authors/maintains only; runtime is deterministic.
- **[ADR-002](../ADR-002.md)** — Spec IR → Grounding → Normalize → Resolver → execution; two-level heal; MCP/KDG.
- **[ADR-003](../ADR-003.md)** — single-language TypeScript-on-Node; shared Zod IR; Fastify core; bundled dashboard; MCP-in-CLI.
- **[PLAN-001](../PLAN-001.md)** — the stack + build-order plan these docs give depth to.
- Background analysis: **[DISCUSSION.md](../DISCUSSION.md)** (resolver behavior, scope).

## Canonical conventions (uniform across all docs)

- **Stack:** TypeScript on Node 22+; pnpm + Turborepo; Fastify core; Vite dashboard; MCP in CLI.
- **Signals (5):** `semantics · affordance · context · structure · index` (semantics = local ONNX embedding + cosine; no fuzzy matching).
- **Bands:** `high ≥ 0.7 · medium ≥ 0.5 · low < 0.5`; grounding/runtime accept at `≥ medium`.
- **Artifacts:** `spec.json` (Tier-1, versioned) → `candidates.json` (Tier-2) → grounded test (with `resolution` + `cachedSelector`). Versioned JSON in git; SQLite cache is regenerable.
- **Runtime is LLM-free.** Low confidence → `stale` → author review; LLM re-enters only in explicit maintenance.

## Scope of this pass

**Deep:** authoring, grounding, normalize, resolver, execution+assertions, healing, storage, MCP/CLI.
**Thin (deferred, flagged in-doc):** dashboard component design, KDG internal data structure, network
recorder, benchmarks, coverage methodology, CI, cloud/paid tier.
