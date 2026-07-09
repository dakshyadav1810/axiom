# SPEC-004: The Two-Level Healing Loop

**Status:** Draft
**Implements:** [ADR-002 §5](../../ADR-002.md), [ADR-001](../../ADR-001.md)
**LLD:** [LLD-006](../lld/LLD-006-healing.md)

> Axiom heals **location drift** deterministically at runtime and repairs **intent/structural change**
> explicitly with an LLM during maintenance. The two levels are strictly separated: runtime never calls
> an LLM; maintenance is the only place it re-enters.

---

## 1. Two levels at a glance

| | **Runtime heal** | **Maintenance heal** |
|---|---|---|
| Trigger | cached selector misses during a run | a step is `stale` (or a developer requests repair) |
| Who | deterministic resolver (re-ground) | LLM, via MCP, developer-triggered |
| LLM? | **No** | **Yes** (authoring-time model) |
| Outcome | healed (flag+log) or `stale` | re-authored → re-grounded → reviewed |
| Autonomy | automatic | explicit |

## 2. Runtime heal (deterministic, LLM-free)

When a step's `cachedSelector` no longer uniquely resolves:

```
cached selector miss
   │
   ▼
re-ground this step (extract candidates → resolver)   [LLD-003 §7, LLD-004]
   │
band ≥ medium ?
   ├─ yes → HEALED: use the new winner, update cachedSelector, FLAG + LOG the change, continue the run
   └─ no  → STALE:  stop trusting this step, mark it for author review, fail the run
```

- **Heal is a re-derivation, not a guess.** It only accepts a new element at band ≥ medium with margin.
- **Every heal is visible.** A healed step is flagged in the `RunReport` (selection source = `resolver`)
  and logged with old→new selector, so drift is observable — frequent heals on one step signal that its
  spec target should be tightened.
- **No persistence of a wrong guess.** Only a confident heal updates the cache.

## 3. When a step goes stale

A step is `stale` when runtime heal cannot re-locate it with confidence. Stale means:
- the run **fails** (SPEC-003 §5);
- the step is queued for **author review** (dashboard/CLI), with the failing page snapshot + the top
  low-band candidates;
- **no LLM is invoked** — resolution waits for an explicit maintenance action.

Stale is drift the deterministic system honestly can't resolve (major redesign, element removed, semantic
identity changed). It is surfaced, not hidden.

## 4. Maintenance heal (explicit, LLM-assisted)

A developer (or agent via MCP `healing`) repairs a stale test:

```
repair payload = { Spec IR, Test Case, KDG }        [what the LLM needs to reason about the change]
   │
   ▼
LLM re-authors the affected Tier-1 target(s)         (SPEC-001 rules; DOM-blind)
   │
   ▼
re-ground the affected step(s)                        (SPEC-002)
   │
   ▼
developer reviews the diff → accept → store           (versioned)
```

The repair is **layer-targeted**: a broken selector re-grounds without touching intent; a genuinely
changed intent re-authors the target without discarding the rest of the test.

## 5. What heals vs. what doesn't

- **Heals (runtime):** attribute/id/testid churn, class changes, DOM re-ordering, relocation within the
  same region, minor text changes, wrapper changes — anything where enough signals still uniquely identify
  the element.
- **Does not heal (→ stale → maintenance):** removed elements, unreached state, full semantic-identity
  change with no surviving anchor, ambiguous repeats with no disambiguator, simultaneous semantic +
  structural redesign.
- **Never "healed" by the resolver:** an **assertion** failure. If the element was found but the app
  behaved wrong, that's a real bug reported as a failure — healing does not touch it (SPEC-003 §7).

## 6. Definition of done

Runtime heal is done when the step is either healed (confident re-derivation, logged) or `stale`.
Maintenance heal is done when the re-authored + re-grounded step passes review and the versioned test is
updated. The audit log of heals/stales is the corpus for tightening targets and tuning bands.
