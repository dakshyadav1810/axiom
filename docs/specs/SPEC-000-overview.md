# SPEC-000: Product Overview, Glossary & Doc Map

**Status:** Draft
**Audience:** everyone (product, engineering, contributors, coding agents)
**Sources of truth:** [ADR-001](../adr/ADR-001.md), [ADR-002](../adr/ADR-002.md), [ADR-003](../adr/ADR-003.md), [PLAN-001](../PLAN-001.md), [AGENTS.md](../../AGENTS.md)

> This is the entry point to the Axiom design suite. It frames the product, defines the vocabulary
> every other doc uses, and maps the docs to the decisions they implement. Read it first.

---

## 1. What Axiom is

Axiom is an open-source, **deterministic-first** end-to-end testing platform for AI-native teams. A
developer (or a coding agent) describes a test in natural language — *"test the login flow"* — and Axiom
compiles it into a durable, version-controlled test that runs **without an LLM at runtime**.

The differentiator is the **Multi-Signal Resolver**: instead of one brittle CSS selector per element,
Axiom identifies each element by five independent signals and re-derives it deterministically when the
UI changes. LLM intelligence lives only in **authoring** and explicit **maintenance** — never in the hot
path of a test run.

### The two problems it kills
- **Selector drift** — a class rename or DOM reshuffle breaks a hand-written selector. The resolver
  heals deterministically from the surviving signals.
- **The coverage illusion** — green suites that assert nothing meaningful. Axiom tests carry explicit
  UI/API/DB assertions and report real coverage.

---

## 2. Design principles (inherited from the ADRs)

1. **Intelligence in authoring, determinism in execution.** (ADR-001) The runtime is a pure function of
   the stored test + the live app. No generative LLM call at test time.
2. **Durable intent and volatile grounding are separate artifacts.** (ADR-002) The LLM authors intent;
   the browser grounds it; only deterministic code runs the test.
3. **One language, one runtime, one IR.** (ADR-003) All TypeScript on Node; one Zod schema shared by
   every package.
4. **The resolver is deterministic-first.** Its semantic signal is a *local, fixed-weight embedding
   model* (no network, no generation), not a runtime LLM.

---

## 3. Personas

| Persona | Uses Axiom to… | Primary surface |
|---|---|---|
| **Developer** | author, review, run, and maintain tests locally | CLI (`npx axiom`) + dashboard |
| **Coding agent** (e.g. Claude Code) | author/repair tests programmatically | MCP server (via CLI) |
| **CI** *(future, thin)* | run the committed test suite deterministically | CLI in CI mode |

---

## 4. Glossary (canonical vocabulary — used identically across all docs)

| Term | Meaning |
|---|---|
| **Intent** | the natural-language description of what to test. Input to authoring. |
| **Spec IR** (`spec.json`) | the LLM-authored, **DOM-blind**, versioned test specification. **Tier-1** only. |
| **Tier-1 (semantic) target** | element descriptor the LLM can write without seeing the page: `label`, `semantics[]`, `role`, `actions[]`, `intent`. |
| **Tier-2 (structural) anchors** | element data that only exists once a real page renders: selectors (css/xpath), attributes, geometry, structure, nearby text. Written by grounding. |
| **Grounding** | a single deterministic live run that captures Tier-2 anchors + ranked candidates for each step. |
| **`candidates.json`** | grounding's output: the ranked candidate elements + signals per step. |
| **Grounded test** | `spec.json` merged with resolution results — the runnable artifact, with a `cachedSelector` per target. |
| **Candidate** | one interactive DOM element considered for a step, extracted live from the page. |
| **Signal** | one of the five deterministic scoring dimensions: **semantics, affordance, context, structure, index**. |
| **Resolver** | deterministic engine that scores candidates against a target and picks a winner. |
| **Band** | confidence tier of a resolution: **high** (`≥0.7`), **medium** (`≥0.5`), **low** (`<0.5`). |
| **`cachedSelector`** | the fast-path locator string chosen at grounding, stored in the SQLite cache. |
| **Stale** | a step whose element could not be located deterministically; queued for author review. No runtime LLM. |
| **Runtime heal** | the deterministic re-grounding attempt when the cached selector misses. LLM-free. |
| **Maintenance heal** | the explicit, developer-triggered repair that re-invokes the LLM (via MCP). |
| **Repair payload** | `{ Spec IR, Test Case, KDG }` handed to the LLM during maintenance heal. |
| **KDG** | Knowledge/Dependency Graph — versioned app-structure context the LLM reads at authoring (conditionals + parent/child). Internal data structure TBD. |
| **MCP server** | the agent-facing control plane hosted by the CLI; tools proxy to core over REST/WS. |
| **Test Case** | one runnable test. **One Spec IR ⇒ one Test Case.** |
| **Suite** | a collection of Test Cases (collection of Spec IRs ⇒ intents ⇒ test cases ⇒ suite). |

---

## 5. Artifact lifecycle (the spine)

```
Intent ──authoring(LLM via MCP)──▶ spec.json ──grounding(live run)──▶ candidates.json
                                       │                                     │
                                       └────────── normalize ────────────────┘
                                                     │
                                                     ▼
                                             resolve → grounded test (+ cachedSelector)
                                                     │
                                          ┌──────────┴──────────┐
                                    runtime run            SQLite cache
                                    (deterministic)         (regenerable)
```

- **Versioned in git (source of truth):** `spec.json`, the grounded test.
- **Regenerable cache (SQLite, never committed):** cached selectors, resolution results, embeddings,
  run history, screenshots.

---

## 6. Top-level user journeys (detailed in the SPEC docs)

1. **Author** a test from intent → `spec.json` (SPEC-001).
2. **Ground** it on first run → `candidates.json` + grounded test (SPEC-002).
3. **Run** it deterministically, with assertions and a verdict (SPEC-003).
4. **Heal** it — runtime (deterministic) or maintenance (LLM) — when it drifts (SPEC-004).
5. **Operate** it — CLI commands, MCP tools, dashboard views (SPEC-005).

---

## 7. Invariants (from AGENTS.md — every doc must honor these)

1. The **core (TypeScript/Node)** owns execution.
2. Tests are stored as **JSON**; never generate Playwright scripts as the primary artifact.
3. The **dashboard never executes** tests.
4. The **CLI never executes** tests.
5. The resolver is **deterministic-first**; the semantic signal is a local embedding model, not a
   runtime LLM. Low confidence → **stale/author-review**, not an automatic LLM call.
6. Business logic lives **inside core**.
7. Cross-package communication is **only** REST/WebSocket. MCP tools proxy to core; no internal
   cross-package calls.
8. Every major subsystem sits **behind an interface**.

---

## 8. Document map

| Doc | Covers | Implements |
|---|---|---|
| **SPEC-000** (this) | overview, glossary, journeys | ADR-001/002/003 |
| SPEC-001 | authoring flow & rules | ADR-002 §1 |
| SPEC-002 | grounding flow & rules | ADR-002 §2 |
| SPEC-003 | execution + assertions + verdicts | ADR-002 §3–4 |
| SPEC-004 | the two-level healing loop | ADR-002 §5 |
| SPEC-005 | CLI, MCP, dashboard flows | ADR-002 §6 |
| LLD-000 | architecture, monorepo, process model | ADR-003, PLAN-001 |
| LLD-001 | the shared Zod IR (schemas) | ADR-002 §Artifact model, ADR-003 §2 |
| LLD-002 | authoring implementation | ADR-002 §1 |
| LLD-003 | grounding + normalize implementation | ADR-002 §2 |
| LLD-004 | resolver (5 signals, embeddings) | ADR-002 §3, ADR-003 §4 |
| LLD-005 | execution (dispatcher + adapters) | ADR-002 §4 |
| LLD-006 | healing implementation | ADR-002 §5 |
| LLD-007 | storage (Drizzle/SQLite + artifacts) | ADR-002 §3, ADR-003 §3 |
| LLD-008 | MCP server + REST/WS | ADR-002 §6, ADR-003 §6 |
| LLD-009 | CLI orchestration | ADR-003 §6, PLAN-001 |

**Conventions used everywhere:** bands `high ≥0.7 / medium ≥0.5 / low <0.5`; signals
`semantics · affordance · context · structure · index`; artifacts `spec.json → candidates.json →
grounded test`; stack = TypeScript on Node 22+.
