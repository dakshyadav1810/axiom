# LLD-005: Execution Engine (`core/execution`)

**Status:** Draft
**Implements:** [SPEC-003](../specs/SPEC-003-execution+assert.md), [ADR-002 §4](../adr/ADR-002.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md), [LLD-004](./LLD-004-resolver.md), [LLD-006](./LLD-006-healing.md) (runtimeHeal), [LLD-007](./LLD-007-storage.md)

> Deterministic, LLM-free execution. A **Step Dispatcher** iterates a grounded test and routes each step
> to a **UI / API / DB adapter**; the assertion engine evaluates outcomes; a verdict is aggregated and
> streamed. This replaces the monolithic Python `executor.py` + `test_engine.py` with a dispatcher +
> pluggable adapters.

---

## 1. Module shape

```
core/src/execution/
├── index.ts            # TestRunner (public interface)
├── dispatcher.ts       # StepDispatcher — routes by step.kind, owns per-step lifecycle
├── adapters/
│   ├── ui.ts           # UiAdapter — locate + act via Playwright
│   ├── api.ts          # ApiAdapter — HTTP request/response
│   └── db.ts           # DbAdapter — query + row assertions
├── locate.ts           # cached-selector → resolver-heal → stale ladder
├── assert.ts           # AssertionEngine (UI/API/DB + expectedOutcome + inversion)
├── verdict.ts          # StepResult → RunReport aggregation
├── playwright.ts       # browser/page lifecycle wrapper (shared with grounding)
└── in-page/            # typed modules injected via page.evaluate (former eval strings)
```

## 2. Interfaces

```ts
export interface TestRunner {
  run(test: GroundedTest, opts: { vars?: Vars; emit?: (m: WsMessage) => void }): Promise<RunReport>;
}

export interface StepAdapter {
  readonly kind: StepKind;                       // "ui" | "api" | "db"
  execute(step: Step, ctx: RunContext): Promise<StepResult>;
}
```

`emit` streams `WsMessage`s (run/step/resolver/log) to the WebSocket surface (LLD-008).

## 3. Dispatcher & per-step lifecycle

```ts
async run(test, { vars, emit }) {
  const ctx = await this.openContext(test, vars);        // browser/page + interpolated vars
  const results: StepResult[] = [];
  for (const step of test.steps) {
    emit?.({ type: "step.start", stepId: step.id });
    let r = await this.adapters[step.kind].execute(step, ctx);
    if (r.status === "failed" && step.onFailure === "retry_once") r = await retryOnce(step, ctx);
    results.push(applyOnFailure(step, r));
    emit?.({ type: "step.result", result: r });
    if (isFatal(step, r)) break;                          // abort / retry_once exhausted
  }
  const report = verdict.aggregate(test, results);
  emit?.({ type: "run.complete", report });
  await this.cache.saveRun(report);                       // regenerable history (LLD-007)
  return report;
}
```

## 4. UI adapter — the locate ladder (`ui.ts` + `locate.ts`)

The ladder is **cache → artifact → runtime heal → stale**. The SQLite `resolution_cache` (LLD-007) is the
runtime fast path and is consulted *first*; the versioned `grounded.json` selector is the durable seed used
when the cache is cold (fresh clone, evicted entry) or the page changed. Both lookups are keyed/validated by
the **current page's `domHash`**, so a materially changed page misses cache and falls through to heal rather
than reusing a stale selector.

```ts
async locate(step, ctx): Promise<LocateResult> {
  const domHash = await ctx.domHash(ctx.page);                   // signature of the current page state

  // 1. runtime fast path — the SQLite selector cache (LLD-007), keyed by (testId, stepId, domHash)
  const hit = ctx.cache.getSelector(ctx.testId, step.id, domHash);
  if (hit && await isUniqueVisible(ctx.page.locator(hit.cachedSelector)))
    return { locator: ctx.page.locator(hit.cachedSelector), source: "cached" };

  // 2. durable seed — the selector baked into the grounded artifact at grounding time
  const seed = step.target?.resolution?.cachedSelector;
  if (seed && await isUniqueVisible(ctx.page.locator(seed))) {
    ctx.cache.putSelector({ testId: ctx.testId, stepId: step.id, domHash, cachedSelector: seed, band: step.target!.resolution!.band });
    return { locator: ctx.page.locator(seed), source: "cached" };  // warm the cache for this domHash
  }

  // 3. deterministic runtime heal (re-ground this step). The healing service — the single owner of the
  //    heal state machine (LLD-006) — writes the new selector to cache + audit on success.
  const outcome = await healing.runtimeHeal(ctx.test, step.id, ctx.page);   // LLD-006 §3
  if (outcome.status === "healed")
    return { locator: ctx.page.locator(outcome.cachedSelector), source: "resolver" };

  return { locator: null, source: "none" };                      // → STALE (SPEC-003 §7)
}
```

Because a confident heal is persisted to the cache under the *new* `domHash`, the next run on the changed
page hits step 1 directly — the same step is not re-healed every run. The **versioned artifact is never
rewritten at run time** (§9); only the regenerable cache changes.

Then `act()` dispatches the Playwright action for `step.action` (click/type/select/keypress/submit/…).
`navigate`/`wait` skip location. All in-page DOM logic lives in typed `in-page/` modules (no string-eval).

## 5. API & DB adapters

- **ApiAdapter:** issues the `step.request` (fetch/undici), captures status + body, runs `apiStatus`/
  `apiBody` assertions. No browser needed.
- **DbAdapter:** runs `step.query` against the configured test DB (read-only by default), evaluates
  `dbRow`. Used for unified end-to-end assertions ("the order row exists after checkout").

Both share the `AssertionEngine` and produce the same `StepResult` shape, so a suite freely mixes UI, API,
and DB steps.

## 6. Assertion engine (`assert.ts`)

- Evaluates `preconditions`, `expectedOutcome[]`, and `assertions[]` per SPEC-003 §3–4.
- Implements **negative-test inversion** (SPEC-003 §6): when `step.negative === true` (LLD-001 §3), invert
  `passed`/`failed` for that step deterministically — a correct app rejection passes, a wrong acceptance fails.
- Distinguishes **locate failure** (→ `stale`) from **assertion failure** (→ `failed`) — never conflates
  drift with a real bug (SPEC-003 §7).

## 7. Verdict aggregation (`verdict.ts`)

- Run `passed` iff no step `failed` and ≥1 step executed; `stale` steps fail the run and set
  `RunReport.needsReview = true` (LLD-001 §7), consumed by healing (LLD-006).
- Assigns a `failureClass` (timeout → stale/resolver → assertion/contract → network → action).
- Emits `RunReport` (LLD-001 §7); persists history + screenshots to cache.

## 8. Playwright lifecycle (`playwright.ts`)

One wrapper owns browser/context/page creation, timeouts (`config.timeouts`), screenshot capture, and
teardown — shared by grounding (LLD-003) and execution but never sharing live state across a boundary
(only serialized `DomCandidate`s cross into the resolver).

## 9. Determinism & boundaries

- No generative LLM anywhere in this module. The only "intelligence" is the deterministic resolver
  (LLD-004), invoked through `healing.runtimeHeal` (LLD-006), which owns the re-ground state machine.
  Execution never calls `grounding.reground` directly and never persists a heal decision itself.
- Execution reads the grounded test + cache; it writes only regenerable artifacts (run history,
  screenshots) — never the versioned spec/grounded test.
