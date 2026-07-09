# LLD-006: Healing (`core/healing`)

**Status:** Draft
**Implements:** [SPEC-004](../specs/SPEC-004-healing.md), [ADR-002 §5](../../ADR-002.md)
**Depends on:** [LLD-003](./LLD-003-grounding+normalize.md) (reground), [LLD-004](./LLD-004-resolver.md), [LLD-002](./LLD-002-authoring.md) (maintenance), [LLD-007](./LLD-007-storage.md)

> Two coordinated mechanisms behind one small surface: a **deterministic runtime re-ground loop** (called
> from execution) and a **maintenance repair-payload builder** (called by a developer/agent). Runtime
> never touches an LLM; maintenance is the only LLM re-entry point.

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
  /** Build the { Spec IR, Test Case, KDG } payload for a stale test. */
  buildRepairPayload(testId: string): Promise<RepairPayload>;
  /** Maintenance: re-author (LLM) → re-ground → return a reviewable diff. */
  maintain(testId: string, stepIds: string[]): Promise<RepairResult>;
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

## 6. Maintenance heal (`repair.ts`)

```ts
async maintain(testId, stepIds) {
  const payload = await this.buildRepairPayload(testId);     // { specIR, testCase, kdg }
  const patched = await authoring.submit(                    // LLM re-authors Tier-1 targets (LLD-002)
    await llmRepair(payload, stepIds));                      //   via MCP / provider — DOM-blind
  const reground = await grounding.ground(patched, {});      // re-ground affected steps (LLD-003)
  return diffForReview(testId, reground);                    // developer accepts → store versioned
}
```

- **`RepairPayload = { specIR, testCase, kdg }`** (ADR-002) — exactly the context the LLM needs: the
  durable intent, the current (stale) grounded test, and the app's KDG.
- Maintenance is **explicit** (developer/agent-triggered via MCP `healing`), never automatic at runtime.
- Output is a **diff for review**, not an auto-commit — the human/agent approves before the versioned test
  changes.

## 7. Boundaries

- `runtimeHeal` is pure-deterministic (resolver only); it lives on the run's hot path and must be fast.
- `maintain` is the sole LLM re-entry after authoring; it reuses the authoring service (LLD-002) and
  grounding (LLD-003) rather than duplicating them.
- Healing writes audit + review + cache (regenerable) and, on accepted maintenance, the versioned test via
  storage (LLD-007).
