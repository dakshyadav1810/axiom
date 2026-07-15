# Contributing to Axiom

Axiom is a pnpm + Turborepo monorepo: `packages/shared` (Zod IR), `packages/core` (Fastify server —
resolver, grounding, execution, healing, authoring, storage), `packages/cli` (commander + MCP server),
`packages/dashboard` (Vite + React SPA).

## Development setup

```bash
git clone https://github.com/dakshyadav1810/axiom.git
cd axiom
pnpm install
pnpm build
```

Run a single package in watch mode, e.g. the core server:

```bash
pnpm --filter @axiom/core dev
```

Run tests and typecheck before opening a PR:

```bash
pnpm test
pnpm --filter @axiom/shared exec tsc --noEmit
pnpm --filter @axiom/core exec tsc --noEmit
pnpm --filter @axiom/cli exec tsc --noEmit
pnpm --filter @axiom/dashboard exec tsc --noEmit
```

Lint/format with [Biome](https://biomejs.dev):

```bash
pnpm lint
pnpm format
```

## Architecture

Read [AGENTS.md](AGENTS.md) first — it's the authoritative source on architectural invariants (e.g. the
resolver is deterministic-first; no LLM runs outside authoring/maintenance). The full design is in
[docs/](docs/): [docs/specs](docs/specs) for behavior, [docs/lld](docs/lld) for implementation detail,
[docs/adr](docs/adr) for the decisions behind the stack.

## Making changes

- Keep the resolver deterministic — no network calls, no generative model, in `packages/core/src/resolver`.
- Business logic lives in `packages/core`. The CLI and dashboard only call core over REST/WebSocket.
- New Zod schemas / DTOs go in `packages/shared` — it's the single source of truth for every data shape.
- Update the relevant `docs/specs`/`docs/lld` file alongside a behavioral change; keep them accurate.

## Reporting issues

Open a [GitHub issue](https://github.com/dakshyadav1810/axiom/issues) with repro steps. For resolver
mis-locates, include the target's Tier-1 fields (`label`/`semantics`/`role`) and, if possible, the
candidate list from `candidates.json`.

## Pull requests

- Keep PRs scoped to one concern.
- Add/update tests for anything in `packages/core/src/resolver` or `packages/shared/src/schema`.
- Note any architectural decision in `docs/DECISIONS.md` if the PR makes one.
