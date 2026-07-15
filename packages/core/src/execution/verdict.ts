import type { GroundedTest, RunReport, StepResult } from "@axiom/shared";

// Run passes iff no step failed and >=1 step executed; stale sets needsReview (SPEC-003 §5, LLD-005 §7).
export function aggregate(
  runId: string,
  test: GroundedTest,
  results: StepResult[],
  startedAt: string,
): RunReport {
  const executed = results.filter((r) => r.status !== "skipped");
  const hasFailed = results.some(
    (r) => r.status === "failed" || r.status === "stale",
  );
  const needsReview = results.some((r) => r.status === "stale");
  return {
    runId,
    testId: test.flow.id,
    status: !hasFailed && executed.length > 0 ? "passed" : "failed",
    needsReview,
    steps: results,
    startedAt,
    finishedAt: new Date().toISOString(),
  };
}
