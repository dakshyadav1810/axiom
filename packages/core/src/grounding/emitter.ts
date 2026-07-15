import type {
  GroundedResolution,
  GroundedStep,
  SpecIR,
  Step,
} from "@axiom/shared";

// Merge a winner-only resolution into a UI step's target, producing the grounded step shape.
export function mergeResolution(
  step: Step,
  resolution: GroundedResolution | undefined,
): GroundedStep {
  if (step.kind !== "ui") return step;
  if (!step.target) return { ...step, target: undefined };
  return { ...step, target: { ...step.target, resolution } };
}

export function toGroundedTest(
  spec: SpecIR,
  steps: GroundedStep[],
  groundedUrl: string,
) {
  return {
    ...spec,
    groundedAt: new Date().toISOString(),
    groundedUrl,
    steps,
  };
}
