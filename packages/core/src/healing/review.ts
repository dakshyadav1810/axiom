import type { Candidate } from "@axiom/shared";
import type { CacheStore } from "../cache/index.js";

export function enqueue(
  cache: CacheStore,
  testId: string,
  stepId: string,
  url: string,
  topCandidates: Candidate[],
): void {
  cache.enqueueReview({
    testId,
    stepId,
    url,
    candidatesJson: JSON.stringify(topCandidates),
  });
}
