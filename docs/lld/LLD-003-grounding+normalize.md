# LLD-003: Grounding + Normalize (`core/grounding`)

**Status:** Draft
**Implements:** [SPEC-002](../specs/SPEC-002-grounding.md), [ADR-002 §2](../adr/ADR-002.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md), [LLD-004](./LLD-004-resolver.md) (resolver), [LLD-007](./LLD-007-storage.md) (cache/artifacts)

> Grounding drives a live Playwright run over an authored spec, extracts candidates, resolves each Tier-1
> target against them, and writes back Tier-2 anchors + a `cachedSelector`. Normalize is the small,
> shared adapter that shapes `(target, live candidates)` into the resolver's input.

---

## 1. Module shape

```
core/src/grounding/
├── index.ts            # GroundingService
├── dom-extractor.ts    # extract live interactive elements + anchors (typed in-page module)
├── candidate.ts        # DomCandidate builder (signals inputs, anchors)
├── normalize.ts        # (target, DomCandidate[]) → ResolverInput  (shared shape)
├── gate.ts             # band ≥ medium accept gate + ungrounded handling
└── emitter.ts          # merge resolution into spec → GroundedTest; write candidates.json
```

## 2. Interface

```ts
export interface GroundingService {
  ground(spec: SpecIR, opts: { vars?: Vars }): Promise<GroundingOutcome>;
  // Single-step re-ground used by runtime heal (LLD-006). It operates on the live page the caller
  // (execution) is already driving — grounding does NOT open its own browser here.
  reground(test: GroundedTest, stepId: string, page: Page): Promise<StepResolution>;
}

export type GroundingOutcome = {
  candidates: CandidatesDoc;       // per-step resolutions (LLD-001 §5)
  grounded: GroundedTest;          // merged runnable artifact (LLD-001 §6)
  stoppedAt?: string;              // stepId where advancing halted (first ungrounded)
};
```

## 3. The `ground()` loop

```ts
const page = await browser.launch(config).newPage();
await page.goto(spec.flow.startUrl);
for (const step of spec.steps) {
  if (!await checkPreconditions(page, step)) { mark(step, "ungrounded", "precondition"); break; }
  if (isNonTargetStep(step)) { await act(page, step); continue; }   // wait / navigate

  const cands = await extractCandidates(page);                      // dom-extractor + candidate.ts
  const input = normalize(step.target!, cands);                     // → ResolverInput
  const resolution = resolver.resolve(input);                       // LLD-004 (pure)

  if (gate.accept(resolution.band)) {                               // band ≥ medium
    step.target!.resolution = withCachedSelector(resolution);       // winner-only + cachedSelector
    await act(page, step);                                          // ACT-to-advance
  } else {
    step.target!.resolution = { ...toWinnerOnly(resolution), status: "ungrounded", selected: null, winner: null, cachedSelector: null };
    outcome.stoppedAt = step.id;                                    // dependent steps unreachable
    break;
  }
}
```

- **ACT-to-advance** (SPEC-002 §3): a grounded step performs its action so step *N+1* sees the right
  state; the first `ungrounded` step halts advancement and returns a **partial** grounded test for review.
- **Partial grounding is valid** (LLD-001 §6): the halting step carries `status: "ungrounded"`; every
  step *after* it is never reached, so its `target.resolution` is left **absent** (the field is optional).
  The full ranked candidate list is written to `candidates.json`; the grounded test stores only the
  winner (`withCachedSelector` returns a winner-only `GroundedResolution`).

## 4. `dom-extractor.ts` — typed in-page module

Replaces the old Python `page.evaluate` strings with a typed module bundled and injected via
`page.evaluate(fn)`. It collects **interactive** elements
(`button,a,input,select,textarea,[role=button|link|textbox|checkbox|radio|menuitem|tab],[tabindex],[onclick]`)
and, per element, computes the inputs each signal needs:

| For signal | Extractor captures |
|---|---|
| semantics | visible text, aria-label, placeholder, label-for text, title |
| affordance | tag, role, disabled, visibility, focusability, click affordance |
| context | ancestor chain (≤5), region (form/modal/section), nearby row/card text |
| structure | tag, id, name, classes, `data-*`, a stable CSS path, xpath, accessible name |
| index | sibling index/count under nearest interactive ancestor |

It returns serializable `DomCandidate`s (with `anchors`), never live handles across the boundary.

## 5. `normalize.ts`

Pure function `(Tier1Target, DomCandidate[]) → ResolverInput`. It is the **only** place spec-side data and
DOM-side data meet, and it lives in shared-shaped types so the resolver stays free of extraction details.
It also seeds the semantic embedding request (LLD-004) by passing `target.semantics` + candidate texts.

## 6. `gate.ts` — accept & cachedSelector

- `accept(band) = band !== "low"` (i.e. `confidence ≥ config.bands.medium`).
- `withCachedSelector(resolution)`: pick the winner's most durable locator —
  `testId → id → unique-CSS → role+name` — set `status:"grounded"`, `selected`, `cachedSelector`, and
  persist the choice to the SQLite cache keyed by `(testId, stepId, domHash)` (LLD-007).

## 7. `reground()` (for heal, LLD-006)

Single-step variant: re-extract candidates on the **caller's live page** (passed in by execution) and
resolve one step's target. Returns a `StepResolution` the heal loop uses to decide healed-vs-stale. No
ACT-to-advance (the run is already at that step), and grounding does not open its own browser — it reuses
execution's page so the DOM state matches the run.

## 8. Determinism

Grounding is deterministic given `(spec, page state, config)`: the extractor is ordered, the resolver is
pure (LLD-004), and the embedding model is fixed-weight. The only nondeterminism is the app itself, which
is why grounding is a *capture* step run once, not on every test run.

## 9. Boundaries

- Grounding owns the browser during grounding; execution (LLD-005) owns it during runs — they share the
  Playwright wrapper but not state.
- Grounding writes `candidates.json` + the grounded test via `storage`, and cache entries via `cache`.
- It never calls an LLM.
