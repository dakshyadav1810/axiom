# SPEC-002: Grounding — `spec.json` → `candidates.json` → Grounded Test

**Status:** Draft
**Implements:** [ADR-002 §2](../adr/ADR-002.md)
**LLD:** [LLD-003](../lld/LLD-003-grounding+normalize.md) · **Schema:** [LLD-001 §5–6](../lld/LLD-001-shared-ir.md)

> Grounding is a single deterministic live run that attaches the **Tier-2 structural anchors** an LLM
> cannot fabricate, turning a DOM-blind spec into a runnable, cache-backed test. It is the bridge between
> authoring and execution.

---

## 1. Goal & guarantees

- **Input:** an authored `SpecIR` + `flow.startUrl` + `vars`.
- **Output:** `candidates.json` (ranked candidates per step) and a **grounded test** (`spec.json` merged
  with `resolution` per target, including a `cachedSelector`).
- **Guarantee:** grounding **never invents** anchors — it captures them from the real DOM, or marks the
  step `ungrounded` for author review. It is deterministic and LLM-free.

## 2. The grounding flow (per step, in order)

```
launch browser @ startUrl
FOR EACH step (in order):
   1. gate on preconditions (visible / enabled / modal_open / url_contains)
   2. extract live interactive DOM  → candidate elements (+ their anchors, signals inputs)
   3. resolve(Tier-1 target, candidates) → ranked candidates + winner + band     (LLD-004)
   4. band ≥ medium ?
        YES → write the winner's Tier-2 anchors + cachedSelector into target.resolution ("grounded")
              then PERFORM the action, so the next step observes the correct page state
        NO  → target.resolution.status = "ungrounded"; record top candidates for review; do NOT guess;
              STOP advancing (steps after this are never reached and carry no resolution)
   5. append per-step ranked candidates to candidates.json
persist candidates.json (full ranking) + grounded test (winner-only, versioned)
```

## 3. Business rules

- **Accept gate = band ≥ medium.** A winner is only trusted (and its anchors cached) when its confidence
  band is `medium` or `high` (`≥0.5`). Below that, the step is `ungrounded`.
- **ACT-to-advance.** After a step grounds, grounding performs the action, because step *N+1* is only
  meaningful on the page state step *N* produces (e.g. you can't ground "click Logout" until "click
  Login" has navigated). If a step is `ungrounded`, grounding **stops advancing** past it (later steps
  depend on state it can't reach) and returns the partial grounded test for review.
- **`cachedSelector` choice.** The most durable locator for the winner is chosen, in priority order:
  `data-testid` → stable `id` → unique CSS → role+name. This becomes the runtime fast path.
- **Deterministic.** Same spec + same page ⇒ same grounding. No randomness, no model that generates.
- **Re-ground triggers.** Grounding re-runs when: the spec changes (new/edited step), the developer
  requests it, or the runtime heal loop invokes it (SPEC-004).

## 4. `ungrounded` → author review

An `ungrounded` step means "no candidate was confidently the target." Causes and what review shows:

| Cause | What the reviewer sees | Typical fix |
|---|---|---|
| No text signal (icon-only) | top candidates all low-band | add a `testId` hint / richer `semantics` |
| Ambiguous repeats | ≥2 near-tie candidates | add a disambiguator (index / nearby context) in the spec |
| Element absent / wrong state | zero candidates | fix step order or preconditions |
| Wrong role/name authored | candidates unrelated | correct the Tier-1 target |

Review happens in the dashboard (candidate list + screenshot) or CLI. After a fix, grounding re-runs.

## 5. What grounding captures per candidate

For each considered element (persisted in `candidates.json`, LLD-001 §5): a concrete `selector`, the
five `signals` scores, `score`+`band`, and **Tier-2 anchors** — `testId`, `attributes`, `xpath`,
`contextPath`, `siblingIndex`, `nearbyText`, `boundingBox`. These anchors are what make the runtime
resolver strong enough to heal later.

The **full ranked list** stays in `candidates.json`. The versioned **grounded test** stores only the
**winner** (winner-only `resolution`, LLD-001 §6), so a UI reshuffle churns `candidates.json` rather than
the durable grounded artifact.

## 6. Definition of done

Grounding "succeeds" when every actionable step reaches `status: grounded` (band ≥ medium) with a
`cachedSelector`, and the grounded test validates as `GroundedTest`. A spec with any `ungrounded` step is
**not runnable** until reviewed and re-grounded.
