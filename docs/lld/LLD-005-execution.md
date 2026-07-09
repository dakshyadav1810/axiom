# LLD-005: Execution Engine (`core/execution`)

**Status:** Draft
**Implements:** [SPEC-003](../specs/SPEC-003-execution+assert.md), [ADR-002 §4](../../ADR-002.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md), [LLD-004](./LLD-004-resolver.md), [LLD-003](./LLD-003-grounding+normalize.md) (reground), [LLD-007](./LLD-007-storage.md)

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

```ts
async locate(step, ctx): Promise<LocateResult> {
  const sel = step.target?.resolution.cachedSelector;
  if (sel) {
    const loc = ctx.page.locator(sel);
    if (await isUniqueVisible(loc)) return { locator: loc, source: "cached" };
  }
  // cached miss → deterministic resolver heal (re-ground this step)
  const res = await grounding.reground(ctx.test, step.id);       // LLD-003 §7
  if (res.band !== "low") {
    ctx.cache.updateSelector(step.id, res.cachedSelector);       // flag "healed" + log
    return { locator: ctx.page.locator(res.cachedSelector!), source: "resolver" };
  }
  return { locator: null, source: "none" };                      // → STALE (SPEC-003 §7)
}
```

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
- Implements **negative-test inversion** (SPEC-003 §6): if the spec declares an expected rejection, invert
  `passed`/`failed` for that step deterministically.
- Distinguishes **locate failure** (→ `stale`) from **assertion failure** (→ `failed`) — never conflates
  drift with a real bug (SPEC-003 §7).

## 7. Verdict aggregation (`verdict.ts`)

- Run `passed` iff no step `failed` and ≥1 step executed; `stale` steps fail the run and set a
  `needsReview` flag consumed by healing (LLD-006).
- Assigns a `failureClass` (timeout → stale/resolver → assertion/contract → network → action).
- Emits `RunReport` (LLD-001 §7); persists history + screenshots to cache.

## 8. Playwright lifecycle (`playwright.ts`)

One wrapper owns browser/context/page creation, timeouts (`config.timeouts`), screenshot capture, and
teardown — shared by grounding (LLD-003) and execution but never sharing live state across a boundary
(only serialized `DomCandidate`s cross into the resolver).

## 9. Determinism & boundaries

- No generative LLM anywhere in this module. The only "intelligence" is the deterministic resolver
  (LLD-004) invoked through `grounding.reground`.
- Execution reads the grounded test + cache; it writes only regenerable artifacts (run history,
  screenshots) — never the versioned spec/grounded test.
