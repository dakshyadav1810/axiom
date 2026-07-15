import { z } from "zod";
import { Step } from "./step.js";

// spec.json — versioned, DOM-blind (LLD-001 §4)
export const SpecIR = z.object({
  version: z.literal("1.0"),
  flow: z.object({
    id: z.string(),
    name: z.string(),
    intent: z.string(),
    startUrl: z.string().url(),
    // declared var NAMES + optional non-secret defaults; secret values arrive via RunRequest.vars
    vars: z.record(z.string()).default({}),
  }),
  steps: z.array(Step).min(1),
});
export type SpecIR = z.infer<typeof SpecIR>;

// spec lint (LLD-002 §5): every ${var} used must exist in flow.vars; actuating UI steps need a target;
// wait/navigate must not have one; at least one assertion/expectedOutcome across the spec.
export function lintSpec(spec: SpecIR): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
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
        "submit",
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
