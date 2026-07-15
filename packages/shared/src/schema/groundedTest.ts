import { z } from "zod";
import { GroundedResolution } from "./resolution.js";
import { SpecIR } from "./spec.js";
import { ApiStep, DbStep, UiStep } from "./step.js";
import { Tier1Target } from "./target.js";

// resolution optional: steps past the first ungrounded step are never reached (LLD-003 ACT-to-advance)
export const GroundedTarget = Tier1Target.extend({
  resolution: GroundedResolution.optional(),
});
export type GroundedTarget = z.infer<typeof GroundedTarget>;

export const GroundedUiStep = UiStep.omit({ target: true }).extend({
  target: GroundedTarget.optional(),
});
export type GroundedUiStep = z.infer<typeof GroundedUiStep>;

export const GroundedStep = z.discriminatedUnion("kind", [
  GroundedUiStep,
  ApiStep,
  DbStep,
]);
export type GroundedStep = z.infer<typeof GroundedStep>;

export const GroundedTest = SpecIR.omit({ steps: true }).extend({
  groundedAt: z.string(),
  groundedUrl: z.string().url(),
  steps: z.array(GroundedStep),
});
export type GroundedTest = z.infer<typeof GroundedTest>;

export function isStepGrounded(step: GroundedStep): boolean {
  return step.kind === "ui" && step.target?.resolution?.status === "grounded";
}
