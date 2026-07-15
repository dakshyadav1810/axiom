# LLD-006: Healing (`core/healing`)

**Status:** Draft
**Implements:** [SPEC-004](../specs/SPEC-004-healing.md), [ADR-002 §5](../adr/ADR-002.md)
**Depends on:** [LLD-003](./LLD-003-grounding+normalize.md) (reground), [LLD-004](./LLD-004-resolver.md), [LLD-002](./LLD-002-authoring.md) (maintenance), [LLD-007](./LLD-007-storage.md)

> Two coordinated mechanisms behind one small surface: a **deterministic runtime re-ground loop** (called
> from execution) and a **maintenance repair-payload builder** (called by a developer/agent). Runtime
> never touches an LLM; maintenance never touches one either — the connected agent is the LLM, and it
> always supplies the fix.

---

## 1. Module shape

```
core/src/healing/
├── index.ts          # HealingService
├── runtime.ts        # runtime heal state machine (deterministic)
├── repair.ts         # RepairPayload builder + maintenance orchestration
├── review.ts         # stale queue + author-review records
└── audit.ts          # heal/stale audit log (old→new selector, band, timestamps)
```

## 2. Interface

```ts
export interface HealingService {
  /** Called by execution (LLD-005) on a cached-selector miss. Deterministic, LLM-free. */
  runtimeHeal(test: GroundedTest, stepId: string, page: Page): Promise<HealOutcome>;
  /** Build the { Spec IR, Test Case, KDG } payload for a stale test — for the agent to read. */
  buildRepairPayload(testId: string): Promise<RepairPayload>;
  /**
   * Maintenance: the agent has already re-authored the affected Tier-1 target(s) using the repair
   * payload; core validates the result, re-grounds it, and returns a reviewable diff. There is no
   * path where core itself re-authors the fix — `patchedSpec` is required, not optional.
   */
  maintain(testId: string, stepIds: string[], patchedSpec: SpecIR): Promise<RepairResult>;
}

export type HealOutcome =
  | { status: "healed";  cachedSelector: string; band: Band; from: string | null }
  | { status: "stale";   reason: string; topCandidates: Candidate[] };
```

## 3. Runtime heal state machine (`runtime.ts`)

```
        cached-selector miss
                 │
                 ▼
        reground(step)  ── resolver.resolve on freshly extracted candidates   [LLD-003 §7]
                 │
        band ≥ medium ?
        ┌────────┴─────────┐
       YES                 NO
        │                   │
   HEALED                 STALE
   • updateSelector()      • enqueue review record (page snapshot + top low-band candidates)
   • audit(from→to,band)   • audit(stale, reason)
   • return healed         • return stale  → execution fails the run + sets needsReview
```

- **Deterministic:** identical to grounding's per-step path; no randomness, no model that generates.
- **Idempotent within a run:** a healed selector is written to cache so subsequent steps/runs use it
  directly.
- **Bounded:** one re-ground attempt per step per run (plus execution's `retry_once` at the step level);
  it does not loop indefinitely.

## 4. Audit (`audit.ts`)

Every heal and stale writes an entry: `{ testId, stepId, event: "healed"|"stale", from, to, band,
reason?, at }`. This audit log is (a) surfaced in the dashboard, (b) the signal that a target needs
tightening (frequent heals), and (c) the corpus for band/weight tuning. Stored in the SQLite cache
(regenerable) — see LLD-007.

## 5. Stale queue & review (`review.ts`)

A stale step produces an **author-review record**: the failing URL, a screenshot, the low-band candidate
list, and the original target. These records back the dashboard/CLI review UI (SPEC-005). A test with any
open review record is `needsReview` and excluded from "green" suite counts until repaired.

## 6. Maintenance heal (`repair.ts`) — one path, agent-supplied

```ts
async maintain(testId, stepIds, patchedSpec) {
  // patchedSpec is required: the agent read buildRepairPayload(testId) via the MCP `healing` tool,
  // re-authored the affected Tier-1 target(s) itself, and is submitting the result here. Core never
  // re-authors anything — there is no provider-calling fallback.
  const spec = await authoring.submit(patchedSpec);          // LLD-002 — validate + store, no generation
  const reground = await grounding.ground(spec, {});         // re-ground affected steps (LLD-003)
  return diffForReview(testId, reground);                    // developer accepts → store versioned
}
```

- **`RepairPayload = { specIR, testCase, kdg }`** (ADR-002) — exactly the context the agent needs to
  reason about the change: the durable intent, the current (stale) grounded test, and the app's KDG.
  Fetched via the MCP `healing` tool or `GET /tests/:id/repair`, read entirely inside the agent's session.
- The repaired spec is a **DOM-blind Tier-1** spec (SPEC-001 rules) — the agent never sees live DOM even
  during maintenance; grounding re-attaches Tier-2 anchors.
- Maintenance is **explicit** (developer/agent-triggered via MCP `healing` + `updateTest`), never automatic
  at runtime, and never something core initiates or generates on its own.
- Output is a **diff for review**, not an auto-commit — the human/agent approves before the versioned test
  changes.

## 7. Boundaries

- `runtimeHeal` is pure-deterministic (resolver only); it lives on the run's hot path and must be fast.
- `maintain` reuses `authoring.submit` (LLD-002) and `grounding.ground` (LLD-003) — it does not duplicate
  either, and it holds no LLM client of its own.
- Healing writes audit + review + cache (regenerable) and, on accepted maintenance, the versioned test via
  storage (LLD-007).
