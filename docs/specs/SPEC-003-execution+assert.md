# SPEC-003: Execution & Assertions — Running a Test, Pass/Fail

**Status:** Draft
**Implements:** [ADR-002 §3–4](../adr/ADR-002.md), [ADR-001](../adr/ADR-001.md)
**LLD:** [LLD-005](../lld/LLD-005-execution.md) · **Schema:** [LLD-001 §3,§7](../lld/LLD-001-shared-ir.md)

> How a grounded test runs deterministically, how each step is located and asserted, and exactly what
> makes a step (and a run) pass, fail, warn, or go stale. No LLM participates at run time.

---

## 1. Goal & guarantees

- **Input:** a grounded test + `vars`.
- **Output:** a `RunReport` — per-step results + an overall verdict, streamed live over WebSocket.
- **Guarantee:** the run is a deterministic function of `(grounded test, live app, vars)`. Location uses
  the selector cache → the grounded artifact's selector → deterministic resolver heal → **stale**; it never
  calls an LLM.

## 2. Per-step lifecycle

```
for each step (in order):
  1. preconditions gate      (visible / enabled / modal_open / url_contains)  → fail = STATE_BLOCKED
  2. LOCATE (UI steps only):
        selector cache hit (keyed by current page's domHash), unique & visible?  ── yes ─▶ use it
        else grounded artifact's cachedSelector, unique & visible?               ── yes ─▶ use it (warm cache)
        else resolver heal (re-ground this step):
               band ≥ medium → use winner, write to cache (flag "healed")
               else          → STALE
  3. ACT                      (click/type/select/… via the UI adapter; or API/DB request)
  4. ASSERT                   (preconditions met + expectedOutcome + assertions + signals)
  5. record StepResult        (status, selection source, band, timing, screenshot)
```

## 3. Assertion types (unified UI + API + DB)

| Kind | Passes when |
|---|---|
| `urlContains` | current URL contains the expected substring |
| `textContains` | page text contains the expected string |
| `value` | the target field's value equals expected |
| `elementVisible` / `elementAbsent` | the described element is present / absent |
| `apiStatus` | the API step's response status equals expected |
| `apiBody` | a JSON path in the response equals expected |
| `dbRow` | the DB query returns the expected row/value |
| `expectedOutcome` (inline) | `navigation` / `url_change` / `element_appears` / `text_contains` / `field_contains` holds |

Assertions and `expectedOutcome` are evaluated after the action; the step's `assertions[]` are the
primary verdict signal, `expectedOutcome` a lighter inline check.

## 4. Step status

| Status | Meaning |
|---|---|
| **passed** | action executed and all assertions held |
| **failed** | an assertion returned false, or the action threw (NOT_INTERACTABLE / VALIDATION_FAILED / …) |
| **warning** | non-fatal: a slow/timeout step that still succeeded, or a failed step with `onFailure: optional` |
| **skipped** | a disabled/optional step not run (e.g. precondition not applicable) |
| **stale** | the element could not be located deterministically after heal → queued for author review |

`onFailure` controls flow after a failed step: `abort` (stop run), `continue`, `retry_once` (re-execute
once), `optional` (downgrade to warning).

## 5. Run verdict

- **Run passes** iff **no step failed** and **at least one step executed**. `warning`/`skipped` do not
  fail a run; `stale` fails the run *and* sets `RunReport.needsReview = true`, flagging it for maintenance
  (SPEC-004).
- **Failure classification** (priority): timeout → resolver/stale → contract/assertion → network → action.
- The `RunReport` (LLD-001 §7) carries per-step status, the **selection source** (`cached`/`resolver`/
  `none` — so drift is visible), band, timings, and screenshots of key moments.

## 6. Negative tests — expected-outcome inversion

For a step authored as a **negative** case (`negative: true` in the step, LLD-001 §3 — "reject invalid
login", XSS/SQLi probe, double-submit), the intent is that the app *should reject* the input. The runtime
inverts the verdict:

- the app **correctly rejects** (the step "fails" to proceed) → the test **passes**;
- the app **wrongly accepts** (the step succeeds) → the test **fails**.

This is a property of the spec's declared expectation, evaluated deterministically — no LLM.

## 7. Locate failure vs assertion failure (the key distinction)

- **Locate failure → stale.** The resolver couldn't find the element. This is *drift*, not a bug — it
  goes to author review (SPEC-004), never fails silently and never calls an LLM at runtime.
- **Assertion failure → real bug.** The element was found and acted on, but the app behaved wrong. This is
  a genuine test failure and is reported as such. The resolver/heal system never masks it.

## 8. Determinism & parameters

Configurable, but fixed per run: action/nav timeouts, `retry_once` count, band thresholds, margin. Same
inputs ⇒ same verdict. Screenshots and run history persist to the SQLite cache (regenerable), not git.
