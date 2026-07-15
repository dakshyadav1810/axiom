# Axiom

![License: BUSL-1.1](https://img.shields.io/badge/license-BUSL--1.1-blue.svg)

**Testing infrastructure for the AI era — source-available, local-first, no vendor lock-in.**

Axiom replaces brittle CSS/XPath selectors with a **Multi-Signal Relational Resolver**: every element
is located by scoring five independent signals — affordance, semantics, structure, context, and index —
instead of one fragile string. When your UI changes, Axiom re-derives the element deterministically, on
your machine, with no LLM in the loop and no retry-and-hope.

You describe intent in natural language to a coding agent (Claude Code, Cursor, ...) connected over MCP;
Axiom maps your app, resolves the element, and replays the run in a local dashboard so you verify
behavior instead of hand-writing selectors.

> **Status:** pre-release. The CLI is not yet published to npm — see [Development](#development) to run
> it from source today. `npx axiom` below is the target install command once published.

## Table of contents

- [The problem](#the-problem)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Why Axiom](#why-axiom)
- [Features](#features)
- [Roadmap](#roadmap)
- [Tiers](#tiers)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## The problem

- **Brittle selectors.** `div > form > button.btn-blue` breaks on the next class rename or DOM reshuffle
  — not because the feature broke, but because the test was never really testing the feature.
- **The coverage illusion.** Green suites that assert nothing meaningful give false confidence; a passing
  test and a *correct* test are not the same thing.
- **CI thrash.** Selector drift turns into a maintenance treadmill — someone has to open the test file,
  find the new selector, and re-run, every single time the UI changes.
- **Closed-source AI healing.** The tools that do attempt AI-native healing lock your tests into a
  proprietary cloud and bill you per LLM call, every time a test runs.

## Quick start

```bash
npx axiom init      # scaffold .axiom/ + axiom.config.json in your project
npx axiom start      # spawn the local server, mount the MCP server, open the dashboard
```

`axiom start` launches one local process: a Fastify server (default `http://127.0.0.1:4319`), an MCP
server over stdio for your coding agent, and the dashboard, served from that same server. Axiom itself
never calls an LLM provider and holds no API key — whatever your coding agent already talks to (Claude,
GPT, ...) is the only model in the loop, and that's a connection you already have, not one Axiom adds.

Then, from your coding agent (Claude Code, Cursor, or anything that speaks MCP):

```
"Test the login flow" → agent calls the axiom MCP tools → spec.json is authored, grounded, and run
```

See [Development](#development) if you want to run this from source before it's published.

## How it works

### 1. Connect

`axiom start` mounts a local [Model Context Protocol](https://modelcontextprotocol.io) server that
exposes your app's structure and test lifecycle as tools your agent can call directly — `getMap`,
`submitSpec`, `groundTest`, `runTest`, `getReport`, `healing`, `updateTest`, and more.

```
$ npx axiom start
core listening on http://127.0.0.1:4319
```

### 2. Describe

Tell your agent what to test, in plain language. The agent authors a DOM-blind spec — meaning
(`label`, `semantics`, `role`, `intent`), never a selector — then Axiom grounds it against your live app,
resolving each step to a real element via the five-signal resolver:

| Signal | Answers |
|---|---|
| **Semantics** | Does this element mean what the user intended? (local embedding + cosine similarity) |
| **Affordance** | Can it actually perform this action? (visible, enabled, capability match — a hard gate) |
| **Structure** | Can we identify it by what it is? (`data-testid`, `id`, role, tag) |
| **Context** | Is it in the right place? (ancestor chain, region, nearby text) |
| **Index** | Is it identified by position, as a last resort? |

Axiom has no LLM client of its own — authoring only happens through your connected agent's `submitSpec`
MCP call. The bare CLI can ground and run a spec that already exists, but can't create one:

```bash
npx axiom ground <testId>
```

### 3. Verify

Run the test deterministically — no LLM call on this path. A selector miss triggers a local re-ground
against the current DOM (still five-signal, still no model), not a silent failure and not an LLM retry:

```bash
$ npx axiom test
login-flow: passed
```

The dashboard streams each run live and shows per-step status, which locator source was used
(cached vs. freshly resolved), confidence band, and timing, so you can see *why* a step passed, failed,
or needs review instead of re-reading test code.

## Why Axiom

| | **Axiom** | **Playwright / Cypress** | **Closed-source AI testing** (KaneAI, TestSprite-style) |
|---|---|---|---|
| Element resolution | 5-signal deterministic resolver | Static selectors you write by hand | Proprietary, cloud-only |
| Self-healing | Local, deterministic, no LLM call | None | LLM-based, billed per run |
| Where tests live | Your own git repo, as JSON | Your own git repo, as code | Vendor's cloud |
| LLM cost at runtime | None — ever | N/A | Usage-based credits |
| Authoring | Your own Claude/Cursor session via MCP | You write the code | Vendor's model, vendor's bill |
| License | Source-available (BUSL-1.1), free to self-host/modify | Open source (no AI-native healing) | Closed source |

## Features

- **UI flow testing** — multi-step browser flows authored from intent, grounded once, run deterministically.
- **API contract testing** — `apiStatus` / `apiBody` assertions against JSON responses, in the same spec
  as your UI steps, using the same runner.
- **Unified assertions** — UI, API, and DB checks (`urlContains`, `textContains`, `elementVisible`,
  `apiBody`, `dbRow`, ...) in one spec, one run, one report.
- **Local dashboard** — live run log over WebSocket, per-step results (status, locator source, confidence
  band, duration), and a JSON editor for hand-editing specs.
- **MCP-native** — every part of the authoring/grounding/run/heal lifecycle is exposed as an MCP tool, so
  a coding agent drives Axiom the same way a human would over the CLI.
- **Two-level healing** — automatic, deterministic re-grounding on drift; explicit, developer-triggered
  maintenance (via your own LLM session) only when the deterministic path can't recover.

## Roadmap

Not yet built — tracked, not shipped:

- **Coverage visibility** — what fraction of the app is actually under test.
- **Flaky test detection** — surfacing steps that heal repeatedly as a signal to tighten the test, not
  just logging the individual heal events.
- **Visual replay** — screenshot capture per step and a replay view in the dashboard (the schema has a
  slot for this; nothing populates it yet).
- **KDG versioning** (`getDelta`) — diffing the app's knowledge graph across authoring sessions.

## Tiers

- **Local (free, source-available):** the full resolver, the CLI, sequential local execution, the
  dashboard — no license gate, no usage metering, self-host and modify freely. This is what's in this
  repository today.
- **Team/cloud:** not yet available. This is the one use the license carves out — see [License](#license).
  Everything else (self-hosting, modifying, running it yourself) stays free.

## Development

The CLI isn't on npm yet. To run it from source:

```bash
git clone https://github.com/dakshyadav1810/axiom.git
cd axiom
pnpm install
pnpm build
node packages/cli/dist/index.js start
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full dev setup, test/typecheck commands, and the
monorepo layout (`packages/shared`, `packages/core`, `packages/cli`, `packages/dashboard`). The design
docs live in [docs/](docs/) — [docs/specs](docs/specs) for behavior, [docs/lld](docs/lld) for
implementation, [docs/adr](docs/adr) for why the stack looks the way it does.

## Contributing

Issues and PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[Business Source License 1.1](LICENSE) (BUSL-1.1) — **not** an OSI-approved open-source license, but free
to use, self-host, and modify for any purpose. The one thing it blocks: offering Axiom (or a modified
version of it) to third parties as a competing hosted/managed service. Contributing back via a fork/PR is
explicitly fine. On 2030-07-15, this version automatically converts to Apache License 2.0.
