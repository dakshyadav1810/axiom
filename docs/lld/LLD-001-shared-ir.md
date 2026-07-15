# LLD-001: The Shared IR (`packages/shared`)

**Status:** Draft
**Implements:** [ADR-002](../adr/ADR-002.md) (artifact model), [ADR-003 §2](../adr/ADR-003.md)
**Consumed by:** every package. This is the **single source of truth** for all data shapes.

> `packages/shared` holds Zod schemas + inferred types for the whole system. Nothing here has a runtime
> dependency on a sibling package. Every artifact, DTO, and WS message is defined here **once** and
> imported by core, cli, and dashboard. Zod replaces Pydantic; there is no second schema.

Layout: `packages/shared/src/schema/{enums,target,step,spec,candidates,resolution,groundedTest,config,dto,ws}.ts`,
re-exported from `src/index.ts`.

---

## 1. Enums & scalars (`enums.ts`)

```ts
import { z } from "zod";

export const ActionType = z.enum([
  "navigate", "click", "type", "select", "keypress", "submit", "wait",
]);

export const StepKind = z.enum(["ui", "api", "db"]);          // unified UI + API + DB testing

export const Generalization = z.enum([
  "same_element", "any_matching", "aggressive", "flexible",   // resolver strictness
]);

export const OnFailure = z.enum(["abort", "continue", "retry_once", "optional"]);

export const SignalName = z.enum([
  "semantics", "affordance", "context", "structure", "index", // the canonical five
]);

export const Band = z.enum(["high", "medium", "low"]);         // ≥0.7 / ≥0.5 / <0.5
export const ResolutionStatus = z.enum(["grounded", "ungrounded", "stale"]);

export const Score = z.number().min(0).max(1);                 // every signal & final score
```

## 2. Tier-1 target (`target.ts`) — what the LLM authors

DOM-blind. No selectors, geometry, or structure — those are added by grounding (§5).

```ts
export const Tier1Target = z.object({
  label: z.string(),                       // human name of the control ("Email")
  semantics: z.array(z.string()).min(1),   // synonym bag ["email","login","credential"]
  role: z.string(),                        // aria/implicit role ("textbox","button","link")
  actions: z.array(z.string()).default([]),// capabilities the step needs (["type","focus"])
  intent: z.string(),                      // one-line purpose ("Primary email input")
});
export type Tier1Target = z.infer<typeof Tier1Target>;
```

## 3. Step (`step.ts`) — discriminated on `kind`

The **UI step** is the primary shape (resolver-driven). `api`/`db` steps carry no target — they assert
against a backend directly (unified testing per AGENTS.md).

Every precondition is an object with a `kind` discriminator — valueless kinds are still
objects (no bare string members), so the gate has one uniform shape to evaluate.

```ts
export const Precondition = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("visible") }),      // the step target is visible
  z.object({ kind: z.literal("enabled") }),      // the step target is enabled
  z.object({ kind: z.literal("modal_open") }),   // a modal/dialog is open
  z.object({ kind: z.literal("url_contains"), value: z.string() }), // current URL contains value
]);

export const ExpectedOutcome = z.discriminatedUnion("type", [
  z.object({ type: z.literal("navigation") }),
  z.object({ type: z.literal("url_change"),   value: z.string() }),
  z.object({ type: z.literal("element_appears"), value: z.string() }),
  z.object({ type: z.literal("text_contains"), value: z.string() }),
  z.object({ type: z.literal("field_contains"), value: z.string() }),
]);

export const Assertion = z.discriminatedUnion("type", [
  z.object({ type: z.literal("urlContains"),    expected: z.string() }),
  z.object({ type: z.literal("textContains"),   expected: z.string() }),
  z.object({ type: z.literal("value"),          expected: z.string() }),
  z.object({ type: z.literal("elementVisible"), target: Tier1Target }),
  z.object({ type: z.literal("elementAbsent"),  target: Tier1Target }),
  z.object({ type: z.literal("apiStatus"),      expected: z.number() }),
  z.object({ type: z.literal("apiBody"),        path: z.string(), expected: z.unknown() }),
  z.object({ type: z.literal("dbRow"),          query: z.string(), expected: z.unknown() }),
]);

const StepBase = z.object({
  id: z.string(),
  intent: z.string(),
  onFailure: OnFailure.default("abort"),
  preconditions: z.array(Precondition).default([]),
  assertions: z.array(Assertion).default([]),
  negative: z.boolean().default(false),   // negative test: the app SHOULD reject this step;
                                          //   the runtime inverts the verdict (SPEC-003 §6)
});

export const UiStep = StepBase.extend({
  kind: z.literal("ui"),
  action: ActionType,
  value: z.string().optional(),                 // for type/select/keypress
  generalization: Generalization.default("same_element"),
  expectedOutcome: z.array(ExpectedOutcome).default([]),
  target: Tier1Target.optional(),               // omitted for wait/navigate
});

export const ApiStep = StepBase.extend({
  kind: z.literal("api"),
  request: z.object({
    method: z.enum(["GET","POST","PUT","PATCH","DELETE"]),
    url: z.string(),
    headers: z.record(z.string()).optional(),
    body: z.unknown().optional(),
  }),
});

export const DbStep = StepBase.extend({
  kind: z.literal("db"),
  query: z.string(),
});

export const Step = z.discriminatedUnion("kind", [UiStep, ApiStep, DbStep]);
export type Step = z.infer<typeof Step>;
```

## 4. Spec IR (`spec.ts`) — `spec.json`, versioned, DOM-blind

```ts
export const SpecIR = z.object({
  version: z.literal("1.0"),
  flow: z.object({
    id: z.string(),
    name: z.string(),
    intent: z.string(),                         // the original NL goal (audit trail)
    startUrl: z.string().url(),
    vars: z.record(z.string()).default({}),     // declared var names → non-secret default (or "")
  }),
  steps: z.array(Step).min(1),
});
export type SpecIR = z.infer<typeof SpecIR>;
```

> **Secrets never live in the spec.** `flow.vars` declares the variable *names* a test uses and may
> carry non-secret defaults only. Secret values (passwords, tokens) are supplied at run time via
> `RunRequest.vars` (§7) and are never written to `spec.json`/`grounded.json` or committed to git.

There is no authoring-request DTO here — the connected agent composes the `SpecIR` entirely in its own
session and calls `submitSpec` (LLD-008) with the finished spec. Nothing upstream of `submitSpec` is a
shared type, because nothing upstream of it runs inside Axiom.

## 5. Grounding output (`candidates.ts` + `resolution.ts`) — Tier-2

### Candidate — one considered element (grounding-captured, persisted subset)
```ts
export const BoundingBox = z.object({ x:z.number(), y:z.number(), width:z.number(), height:z.number() });

export const SignalScores = z.object({
  semantics: Score, affordance: Score, context: Score, structure: Score, index: Score,
});

export const Candidate = z.object({
  id: z.string(),                                // "cand_2"
  selector: z.string(),                          // a concrete locator for this candidate
  label: z.string().optional(),
  role: z.string().optional(),
  boundingBox: BoundingBox.optional(),
  anchors: z.object({                            // Tier-2 structural anchors
    testId: z.string().optional(),
    attributes: z.record(z.string()).default({}),
    xpath: z.string().optional(),
    contextPath: z.array(z.string()).default([]),
    siblingIndex: z.number().optional(),
    nearbyText: z.string().optional(),
  }).partial().default({}),
  signals: SignalScores,
  score: Score,
  band: Band,
});
export type Candidate = z.infer<typeof Candidate>;
```

### Resolution — the resolver's verdict for one target (embedded in the grounded test)
```ts
export const Resolution = z.object({
  status: ResolutionStatus,                      // grounded | ungrounded | stale
  confidence: Score,
  band: Band,
  selected: z.string().nullable(),               // winning candidate id, null if ungrounded
  cachedSelector: z.string().nullable(),         // fast-path locator, null if ungrounded
  candidates: z.array(Candidate),                // ranked, best first
});
export type Resolution = z.infer<typeof Resolution>;
```

### `candidates.json` — grounding's raw per-step output (pre-merge)
```ts
export const CandidatesDoc = z.object({
  version: z.literal("1.0"),
  specId: z.string(),
  groundedAt: z.string(),                        // ISO8601 (stamped by caller)
  groundedUrl: z.string().url(),
  steps: z.array(z.object({
    stepId: z.string(),
    resolution: Resolution,
  })),
});
```

## 6. Grounded test (`groundedTest.ts`) — the runnable artifact

`spec.json` merged with resolution. The `resolution` rides **inside the target** (matches the discussion
example); a step is grounded iff `target.resolution?.status === "grounded"`.

The grounded artifact stores a **winner-only** resolution — the selected candidate plus its anchors, not
the full ranked list. The complete ranking lives in `candidates.json` (§5), so the volatile per-candidate
detail does not bloat the durable, git-versioned grounded test (and a UI reshuffle churns `candidates.json`,
not `grounded.json`).

```ts
// Winner-only: drops the full `candidates[]`, keeps just the selected candidate.
export const GroundedResolution = Resolution.omit({ candidates: true }).extend({
  winner: Candidate.nullable(),        // the selected candidate + anchors; null if not grounded
});

// `resolution` is OPTIONAL: steps beyond the first ungrounded step are never reached by grounding
// (ACT-to-advance halts, LLD-003 §3), so they carry no resolution yet. Absent ⇒ not grounded.
export const GroundedTarget = Tier1Target.extend({ resolution: GroundedResolution.optional() });

export const GroundedUiStep = UiStep.omit({ target: true }).extend({
  target: GroundedTarget.optional(),
});
export const GroundedStep = z.discriminatedUnion("kind", [GroundedUiStep, ApiStep, DbStep]);

export const GroundedTest = SpecIR.omit({ steps: true }).extend({
  groundedAt: z.string(),
  groundedUrl: z.string().url(),
  steps: z.array(GroundedStep),
});
export type GroundedTest = z.infer<typeof GroundedTest>;
```

## 7. Config, DTOs & WS messages (`config.ts`, `dto.ts`, `ws.ts`)

```ts
export const AxiomConfig = z.object({
  port: z.number().default(4319),
  browser: z.enum(["chromium","firefox","webkit"]).default("chromium"),
  headless: z.boolean().default(true),
  dbPath: z.string().default(".axiom/cache.db"),
  artifactsDir: z.string().default(".axiom/tests"),
  embeddingModel: z.string().default("Xenova/all-MiniLM-L6-v2"),
  bands: z.object({ high: Score.default(0.7), medium: Score.default(0.5) }).default({}),
  timeouts: z.object({ actionMs: z.number().default(15000), navMs: z.number().default(30000) }).default({}),
  // Optional test database for the DB adapter (LLD-005 §5). Absent ⇒ db-kind steps error at run.
  db: z.object({
    url: z.string().optional(),          // connection string; read-only by default
    readOnly: z.boolean().default(true),
  }).default({}),
});
// No `llm` block: core never calls a model provider. Authoring happens entirely inside the developer's
// connected agent (SPEC-001 §2); there is no API key anywhere in this config to hold or leak.

// REST DTOs (validated at the Fastify edge via fastify-type-provider-zod)
// No AuthorRequest: the agent authors the spec itself and calls submitSpec with the finished SpecIR.
export const GroundRequest = z.object({ specId: z.string() });
export const RunRequest = z.object({ testId: z.string(), vars: z.record(z.string()).optional() });

// `spec` is REQUIRED: the agent always supplies the repaired SpecIR (LLD-006 §6). There is no
// omit-it-and-core-generates-the-fix path.
export const MaintainRequest = z.object({ stepIds: z.array(z.string()), spec: SpecIR });

export const StepResult = z.object({
  stepId: z.string(),
  status: z.enum(["passed","failed","warning","skipped","stale"]),
  selection: z.enum(["cached","resolver","none"]).optional(),
  band: Band.optional(),
  failure: z.object({ reason: z.string(), message: z.string() }).optional(),
  durationMs: z.number(),
  screenshot: z.string().optional(),
});
export const RunReport = z.object({
  runId: z.string(), testId: z.string(),
  status: z.enum(["passed","failed"]),
  needsReview: z.boolean().default(false),       // set true when any step went stale (LLD-005 §7)
  steps: z.array(StepResult),
  startedAt: z.string(), finishedAt: z.string(),
});

// WebSocket stream (execution/resolver/log events)
export const WsMessage = z.discriminatedUnion("type", [
  z.object({ type: z.literal("run.start"),    runId: z.string(), testId: z.string() }),
  z.object({ type: z.literal("step.start"),   stepId: z.string() }),
  z.object({ type: z.literal("resolver.event"), stepId: z.string(), band: Band, selected: z.string().nullable() }),
  z.object({ type: z.literal("step.result"),  result: StepResult }),
  z.object({ type: z.literal("log"),          level: z.enum(["info","warn","error"]), line: z.string() }),
  z.object({ type: z.literal("run.complete"), report: RunReport }),
]);
```

## 8. Worked example — one step, authored → grounded

**Authored (`spec.json`, Tier-1 only):**
```json
{
  "id": "s1", "kind": "ui", "action": "type", "value": "${email}",
  "intent": "Enter the user's email address.",
  "generalization": "same_element", "onFailure": "retry_once",
  "preconditions": [{ "kind": "visible" }, { "kind": "enabled" }],
  "expectedOutcome": [{ "type": "field_contains", "value": "${email}" }],
  "assertions": [{ "type": "value", "expected": "${email}" }],
  "target": {
    "label": "Email", "role": "textbox", "intent": "Primary email input",
    "semantics": ["email", "login", "credential"], "actions": ["type", "focus"]
  }
}
```

**Grounded (`target.resolution` populated by the resolver — winner-only):**

The winner leads the runner-up by `0.92 − 0.68 = 0.24 ≥ CONFIDENCE_MARGIN (0.15)`, so `same_element`
accepts it cleanly. Scores use the base weights `semantics 0.45 · context 0.33 · structure 0.22`
(affordance is a 0/1 gate, index a tiebreak — neither is weighted; LLD-004 §5).

```json
"target": {
  "label": "Email", "role": "textbox", "intent": "Primary email input",
  "semantics": ["email","login","credential"], "actions": ["type","focus"],
  "resolution": {
    "status": "grounded", "confidence": 0.92, "band": "high",
    "selected": "cand_2", "cachedSelector": "input[type='email']",
    "winner": {
      "id":"cand_2", "score":0.92, "band":"high", "selector":"input[type='email']",
      "label":"Email", "role":"textbox",
      "signals": {"semantics":0.98,"affordance":1.0,"context":0.84,"structure":0.91,"index":0.5}
    }
  }
}
```

The full ranked list (`cand_1` @ `0.68` medium, `cand_2` @ `0.92` high, …) is persisted separately in
`candidates.json`; only the winner rides in the versioned grounded test.

## 9. Validation rules (enforced in `shared`, checked at every boundary)

- `SpecIR` must parse before grounding; `GroundedTest` before a run. Fastify validates request/response
  DTOs at the edge with `fastify-type-provider-zod`.
- A UI step with `action ∈ {click,type,select,keypress,submit}` **must** have a `target`; `wait`/`navigate` must not.
- Band is derived, never authored: `high` iff `confidence ≥ config.bands.high`, `medium` iff `≥ config.bands.medium`, else `low`.
- `resolution.status`: `grounded` iff `band ≥ medium` and a `selected` winner exists; `ungrounded` if
  grounding reached the step but found nothing acceptable. A step **not reached** by grounding (it halted at
  an earlier ungrounded step) has **no `resolution` at all** (the field is optional/absent).
- `stale` is a **runtime** state: it is recorded in the `review_queue` (LLD-007) when re-grounding fails
  mid-run. The versioned `grounded.json` is **never** rewritten at run time, so `status: "stale"` does not
  appear in a committed artifact — only `grounded` / `ungrounded` / absent do.
- `cachedSelector`/`selected`/`winner` are non-null iff `status === "grounded"`.
- Every `${var}` referenced in a step must exist in `flow.vars` (spec-level lint). Secret values are never
  stored here — they arrive at run time via `RunRequest.vars`.
