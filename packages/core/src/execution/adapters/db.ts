import type { DbStep, StepResult } from "@axiom/shared";
import { evaluateAssertion } from "../assert.js";
import type { RunContext, StepAdapter } from "../types.js";

export class DbAdapter implements StepAdapter {
  readonly kind = "db" as const;

  async execute(step: DbStep, ctx: RunContext): Promise<StepResult> {
    const start = Date.now();
    if (!ctx.dbQuery) {
      return {
        stepId: step.id,
        status: "failed",
        failure: {
          reason: "NO_DB_CONFIGURED",
          message: "config.db.url is not set",
        },
        durationMs: Date.now() - start,
      };
    }
    const row = await ctx.dbQuery(step.query);
    for (const a of step.assertions) {
      const outcome = await evaluateAssertion(a, {
        dbRow: row,
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
