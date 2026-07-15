// src/schema/enums.ts
import { z } from "zod";
var ActionType = z.enum([
  "navigate",
  "click",
  "type",
  "select",
  "keypress",
  "submit",
  "wait"
]);
var StepKind = z.enum(["ui", "api", "db"]);
var Generalization = z.enum([
  "same_element",
  "any_matching",
  "aggressive",
  "flexible"
]);
var OnFailure = z.enum([
  "abort",
  "continue",
  "retry_once",
  "optional"
]);
var SignalName = z.enum([
  "semantics",
  "affordance",
  "context",
  "structure",
  "index"
]);
var Band = z.enum(["high", "medium", "low"]);
var ResolutionStatus = z.enum(["grounded", "ungrounded", "stale"]);
var Score = z.number().min(0).max(1);

// src/schema/target.ts
import { z as z2 } from "zod";
var Tier1Target = z2.object({
  label: z2.string(),
  semantics: z2.array(z2.string()).min(1),
  role: z2.string(),
  actions: z2.array(z2.string()).default([]),
  intent: z2.string()
});

// src/schema/step.ts
import { z as z3 } from "zod";
var Precondition = z3.discriminatedUnion("kind", [
  z3.object({ kind: z3.literal("visible") }),
  z3.object({ kind: z3.literal("enabled") }),
  z3.object({ kind: z3.literal("modal_open") }),
  z3.object({ kind: z3.literal("url_contains"), value: z3.string() })
]);
var ExpectedOutcome = z3.discriminatedUnion("type", [
  z3.object({ type: z3.literal("navigation") }),
  z3.object({ type: z3.literal("url_change"), value: z3.string() }),
  z3.object({ type: z3.literal("element_appears"), value: z3.string() }),
  z3.object({ type: z3.literal("text_contains"), value: z3.string() }),
  z3.object({ type: z3.literal("field_contains"), value: z3.string() })
]);
var Assertion = z3.discriminatedUnion("type", [
  z3.object({ type: z3.literal("urlContains"), expected: z3.string() }),
  z3.object({ type: z3.literal("textContains"), expected: z3.string() }),
  z3.object({ type: z3.literal("value"), expected: z3.string() }),
  z3.object({ type: z3.literal("elementVisible"), target: Tier1Target }),
  z3.object({ type: z3.literal("elementAbsent"), target: Tier1Target }),
  z3.object({ type: z3.literal("apiStatus"), expected: z3.number() }),
  z3.object({
    type: z3.literal("apiBody"),
    path: z3.string(),
    expected: z3.unknown()
  }),
  z3.object({
    type: z3.literal("dbRow"),
    query: z3.string(),
    expected: z3.unknown()
  })
]);
var StepBase = z3.object({
  id: z3.string(),
  intent: z3.string(),
  onFailure: OnFailure.default("abort"),
  preconditions: z3.array(Precondition).default([]),
  assertions: z3.array(Assertion).default([]),
  // negative test: app SHOULD reject; runtime inverts the verdict (SPEC-003 §6)
  negative: z3.boolean().default(false)
});
var UiStep = StepBase.extend({
  kind: z3.literal("ui"),
  action: ActionType,
  value: z3.string().optional(),
  generalization: Generalization.default("same_element"),
  expectedOutcome: z3.array(ExpectedOutcome).default([]),
  target: Tier1Target.optional()
  // omitted for wait/navigate
});
var ApiStep = StepBase.extend({
  kind: z3.literal("api"),
  request: z3.object({
    method: z3.enum(["GET", "POST", "PUT", "PATCH", "DELETE"]),
    url: z3.string(),
    headers: z3.record(z3.string()).optional(),
    body: z3.unknown().optional()
  })
});
var DbStep = StepBase.extend({
  kind: z3.literal("db"),
  query: z3.string()
});
var Step = z3.discriminatedUnion("kind", [UiStep, ApiStep, DbStep]);

// src/schema/spec.ts
import { z as z4 } from "zod";
var SpecIR = z4.object({
  version: z4.literal("1.0"),
  flow: z4.object({
    id: z4.string(),
    name: z4.string(),
    intent: z4.string(),
    startUrl: z4.string().url(),
    // declared var NAMES + optional non-secret defaults; secret values arrive via RunRequest.vars
    vars: z4.record(z4.string()).default({})
  }),
  steps: z4.array(Step).min(1)
});
function lintSpec(spec) {
  const errors = [];
  const varNames = new Set(Object.keys(spec.flow.vars));
  const varRefRe = /\$\{(\w+)\}/g;
  let hasAssertion = false;
  for (const step of spec.steps) {
    const text = JSON.stringify(step);
    for (const m of text.matchAll(varRefRe)) {
      if (!varNames.has(m[1]))
        errors.push(`step ${step.id}: unresolved var \${${m[1]}}`);
    }
    if (step.assertions.length > 0) hasAssertion = true;
    if (step.kind === "ui") {
      if ("expectedOutcome" in step && step.expectedOutcome.length > 0)
        hasAssertion = true;
      const actuating = [
        "click",
        "type",
        "select",
        "keypress",
        "submit"
      ].includes(step.action);
      if (actuating && !step.target)
        errors.push(`step ${step.id}: actuating action requires a target`);
      if (!actuating && step.target)
        errors.push(`step ${step.id}: wait/navigate must not have a target`);
    }
  }
  if (!hasAssertion)
    errors.push("spec has no assertion or expectedOutcome across any step");
  return { ok: errors.length === 0, errors };
}

// src/schema/candidates.ts
import { z as z5 } from "zod";
var BoundingBox = z5.object({
  x: z5.number(),
  y: z5.number(),
  width: z5.number(),
  height: z5.number()
});
var SignalScores = z5.object({
  semantics: Score,
  affordance: Score,
  context: Score,
  structure: Score,
  index: Score
});
var Candidate = z5.object({
  id: z5.string(),
  selector: z5.string(),
  label: z5.string().optional(),
  role: z5.string().optional(),
  boundingBox: BoundingBox.optional(),
  anchors: z5.object({
    testId: z5.string().optional(),
    attributes: z5.record(z5.string()).default({}),
    xpath: z5.string().optional(),
    contextPath: z5.array(z5.string()).default([]),
    siblingIndex: z5.number().optional(),
    nearbyText: z5.string().optional()
  }).partial().default({}),
  signals: SignalScores,
  score: Score,
  band: Band
});

// src/schema/resolution.ts
import { z as z6 } from "zod";
var Resolution = z6.object({
  status: ResolutionStatus,
  confidence: Score,
  band: Band,
  selected: z6.string().nullable(),
  cachedSelector: z6.string().nullable(),
  candidates: z6.array(Candidate)
  // ranked, best first
});
var GroundedResolution = Resolution.omit({ candidates: true }).extend({
  winner: Candidate.nullable()
});
var CandidatesDoc = z6.object({
  version: z6.literal("1.0"),
  specId: z6.string(),
  groundedAt: z6.string(),
  groundedUrl: z6.string().url(),
  steps: z6.array(
    z6.object({
      stepId: z6.string(),
      resolution: Resolution
    })
  )
});

// src/schema/groundedTest.ts
import { z as z7 } from "zod";
var GroundedTarget = Tier1Target.extend({
  resolution: GroundedResolution.optional()
});
var GroundedUiStep = UiStep.omit({ target: true }).extend({
  target: GroundedTarget.optional()
});
var GroundedStep = z7.discriminatedUnion("kind", [
  GroundedUiStep,
  ApiStep,
  DbStep
]);
var GroundedTest = SpecIR.omit({ steps: true }).extend({
  groundedAt: z7.string(),
  groundedUrl: z7.string().url(),
  steps: z7.array(GroundedStep)
});
function isStepGrounded(step) {
  return step.kind === "ui" && step.target?.resolution?.status === "grounded";
}

// src/schema/config.ts
import { z as z8 } from "zod";
var AxiomConfig = z8.object({
  port: z8.number().default(4319),
  browser: z8.enum(["chromium", "firefox", "webkit"]).default("chromium"),
  headless: z8.boolean().default(true),
  dbPath: z8.string().default(".axiom/cache.db"),
  artifactsDir: z8.string().default(".axiom/tests"),
  embeddingModel: z8.string().default("Xenova/all-MiniLM-L6-v2"),
  bands: z8.object({ high: Score.default(0.7), medium: Score.default(0.5) }).default({}),
  timeouts: z8.object({
    actionMs: z8.number().default(15e3),
    navMs: z8.number().default(3e4)
  }).default({}),
  // No `llm` block: Axiom never calls a model provider. Authoring/maintenance happens entirely inside
  // the developer's own connected agent (Claude Code, Cursor, ...) via MCP — there is no API key here.
  db: z8.object({ url: z8.string().optional(), readOnly: z8.boolean().default(true) }).default({})
});

// src/schema/dto.ts
import { z as z9 } from "zod";
var GroundRequest = z9.object({ specId: z9.string() });
var RunRequest = z9.object({ testId: z9.string(), vars: z9.record(z9.string()).optional() });
var MaintainRequest = z9.object({ stepIds: z9.array(z9.string()), spec: SpecIR });
var StepResult = z9.object({
  stepId: z9.string(),
  status: z9.enum(["passed", "failed", "warning", "skipped", "stale"]),
  selection: z9.enum(["cached", "resolver", "none"]).optional(),
  band: Band.optional(),
  failure: z9.object({ reason: z9.string(), message: z9.string() }).optional(),
  durationMs: z9.number(),
  screenshot: z9.string().optional()
});
var RunReport = z9.object({
  runId: z9.string(),
  testId: z9.string(),
  status: z9.enum(["passed", "failed"]),
  needsReview: z9.boolean().default(false),
  steps: z9.array(StepResult),
  startedAt: z9.string(),
  finishedAt: z9.string()
});
var ApiError = z9.object({
  error: z9.object({
    code: z9.enum(["validation", "not_found", "ungrounded", "stale", "browser_error"]),
    message: z9.string(),
    details: z9.unknown().optional()
  })
});
var RepairPayload = z9.object({
  specIR: SpecIR,
  testCase: GroundedTest,
  kdg: z9.unknown()
  // KDG data structure deferred (ADR-002 out-of-scope)
});

// src/schema/ws.ts
import { z as z10 } from "zod";
var WsMessage = z10.discriminatedUnion("type", [
  z10.object({
    type: z10.literal("run.start"),
    runId: z10.string(),
    testId: z10.string()
  }),
  z10.object({ type: z10.literal("step.start"), stepId: z10.string() }),
  z10.object({
    type: z10.literal("resolver.event"),
    stepId: z10.string(),
    band: Band,
    selected: z10.string().nullable()
  }),
  z10.object({ type: z10.literal("step.result"), result: StepResult }),
  z10.object({
    type: z10.literal("log"),
    level: z10.enum(["info", "warn", "error"]),
    line: z10.string()
  }),
  z10.object({ type: z10.literal("run.complete"), report: RunReport })
]);
export {
  ActionType,
  ApiError,
  ApiStep,
  Assertion,
  AxiomConfig,
  Band,
  BoundingBox,
  Candidate,
  CandidatesDoc,
  DbStep,
  ExpectedOutcome,
  Generalization,
  GroundRequest,
  GroundedResolution,
  GroundedStep,
  GroundedTarget,
  GroundedTest,
  GroundedUiStep,
  MaintainRequest,
  OnFailure,
  Precondition,
  RepairPayload,
  Resolution,
  ResolutionStatus,
  RunReport,
  RunRequest,
  Score,
  SignalName,
  SignalScores,
  SpecIR,
  Step,
  StepKind,
  StepResult,
  Tier1Target,
  UiStep,
  WsMessage,
  isStepGrounded,
  lintSpec
};
