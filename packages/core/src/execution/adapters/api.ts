import type { ApiStep, StepResult } from "@axiom/shared";
import { evaluateAssertion } from "../assert.js";
import type { RunContext, StepAdapter } from "../types.js";

function interpolate(s: string, vars: Record<string, string>): string {
  return s.replace(/\$\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}

export class ApiAdapter implements StepAdapter {
  readonly kind = "api" as const;

  async execute(step: ApiStep, ctx: RunContext): Promise<StepResult> {
    const start = Date.now();
    const url = interpolate(step.request.url, ctx.vars);
    const res = await fetch(url, {
      method: step.request.method,
      headers: step.request.headers,
      body: step.request.body ? JSON.stringify(step.request.body) : undefined,
    });
    const body = await res.json().catch(() => undefined);
    for (const a of step.assertions) {
      const outcome = await evaluateAssertion(a, {
        apiResponse: { status: res.status, body },
        vars: ctx.vars,
      });
      if (!outcome.ok) {
        return {
          stepId: step.id,
          status: "failed",
          failure: {
            reason: "ASSERTION_FAILED",
            message: outcome.reason ?? "",
          },
          durationMs: Date.now() - start,
        };
      }
    }
    return {
      stepId: step.id,
      status: "passed",
      durationMs: Date.now() - start,
    };
  }
}
