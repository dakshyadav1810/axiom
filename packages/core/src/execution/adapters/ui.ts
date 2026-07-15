import type { StepResult, UiStep } from "@axiom/shared";
import { act } from "../act.js";
import { evaluateAssertion, evaluateExpectedOutcome } from "../assert.js";
import { locate } from "../locate.js";
import {
  type RunContext,
  type StepAdapter,
  checkPrecondition,
} from "../types.js";

export class UiAdapter implements StepAdapter {
  readonly kind = "ui" as const;

  async execute(step: UiStep, ctx: RunContext): Promise<StepResult> {
    const start = Date.now();
    if (!(await checkPrecondition(step, ctx.page))) {
      return fail(step.id, "STATE_BLOCKED", "precondition not met", start);
    }

    const isTarget = step.action !== "navigate" && step.action !== "wait";
    let selection: StepResult["selection"] = undefined;
    let band: StepResult["band"] = undefined;

    if (isTarget) {
      const groundedStep = ctx.test.steps.find((s) => s.id === step.id);
      if (groundedStep?.kind !== "ui")
        return fail(
          step.id,
          "NOT_GROUNDED",
          "step is not a grounded ui step",
          start,
        );
      const result = await locate(
        ctx.test,
        groundedStep,
        ctx.page,
        ctx.cache,
        ctx.healing,
      );
      selection = result.source;
      if (!result.locator) {
        return {
          stepId: step.id,
          status: "stale",
          selection: "none",
          durationMs: Date.now() - start,
        };
      }
      band = groundedStep.target?.resolution?.band;
    }

    const urlBefore = ctx.page.url();
    try {
      const groundedStep = ctx.test.steps.find((s) => s.id === step.id);
      const cachedSelector =
        groundedStep?.kind === "ui"
          ? (groundedStep.target?.resolution?.cachedSelector ?? null)
          : null;
      await act(ctx.page, step, isTarget ? cachedSelector : null, ctx.vars);
    } catch (e) {
      return maybeInvert(
        step,
        fail(step.id, "ACTION_FAILED", String(e), start),
        selection,
        band,
      );
    }

    for (const outcome of step.expectedOutcome) {
      const res = await evaluateExpectedOutcome(outcome, {
        page: ctx.page,
        urlBefore,
        vars: ctx.vars,
      });
      if (!res.ok)
        return maybeInvert(
          step,
          fail(
            step.id,
            "EXPECTED_OUTCOME_FAILED",
            res.reason ?? "",
            start,
            selection,
            band,
          ),
          selection,
          band,
        );
    }
    for (const a of step.assertions) {
      const res = await evaluateAssertion(a, {
        page: ctx.page,
        vars: ctx.vars,
      });
      if (!res.ok)
        return maybeInvert(
          step,
          fail(
            step.id,
            "ASSERTION_FAILED",
            res.reason ?? "",
            start,
            selection,
            band,
          ),
          selection,
          band,
        );
    }

    const passed: StepResult = {
      stepId: step.id,
      status: "passed",
      selection,
      band,
      durationMs: Date.now() - start,
    };
    return maybeInvert(step, passed, selection, band);
  }
}

function fail(
  stepId: string,
  reason: string,
  message: string,
  start: number,
  selection?: StepResult["selection"],
  band?: StepResult["band"],
): StepResult {
  return {
    stepId,
    status: "failed",
    selection,
    band,
    failure: { reason, message },
    durationMs: Date.now() - start,
  };
}

// SPEC-003 §6: negative tests invert passed/failed — a correct app rejection passes, wrong acceptance fails.
function maybeInvert(
  step: UiStep,
  result: StepResult,
  selection?: StepResult["selection"],
  band?: StepResult["band"],
): StepResult {
  if (!step.negative) return result;
  if (result.status === "passed")
    return {
      ...result,
      status: "failed",
      failure: {
        reason: "NEGATIVE_TEST",
        message: "app accepted input it should have rejected",
      },
    };
  if (result.status === "failed")
    return {
      stepId: step.id,
      status: "passed",
      selection,
      band,
      durationMs: result.durationMs,
    };
  return result;
}
