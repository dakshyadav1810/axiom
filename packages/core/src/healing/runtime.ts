import type { Band, Candidate, GroundedTest } from "@axiom/shared";
import type { Page } from "playwright";
import type { CacheStore } from "../cache/index.js";
import type { GroundingService } from "../grounding/index.js";
import { audit } from "./audit.js";
import { enqueue } from "./review.js";

export type HealOutcome =
  | {
      status: "healed";
      cachedSelector: string;
      band: Band;
      from: string | null;
    }
  | { status: "stale"; reason: string; topCandidates: Candidate[] };

// Deterministic, LLM-free. Called by execution on a cached-selector miss (LLD-006 §3).
// Bounded: one re-ground attempt per step per call — no indefinite looping.
export async function runtimeHeal(
  grounding: GroundingService,
  cache: CacheStore,
  test: GroundedTest,
  stepId: string,
  page: Page,
  previousSelector: string | null,
): Promise<HealOutcome> {
  const result = await grounding.reground(test, stepId, page);

  if (result.band !== "low" && result.cachedSelector) {
    cache.putSelector({
      testId: test.flow.id,
      stepId,
      domHash: result.domHash,
      cachedSelector: result.cachedSelector,
      band: result.band,
    });
    audit(cache, test.flow.id, stepId, "healed", {
      from: previousSelector,
      to: result.cachedSelector,
      band: result.band,
    });
    return {
      status: "healed",
      cachedSelector: result.cachedSelector,
      band: result.band,
      from: previousSelector,
    };
  }

  const topCandidates = result.resolution.candidates.slice(0, 5);
  enqueue(cache, test.flow.id, stepId, page.url(), topCandidates);
  audit(cache, test.flow.id, stepId, "stale", {
    from: previousSelector,
    reason: "no candidate reached medium confidence",
  });
  return {
    status: "stale",
    reason: "no candidate reached medium confidence",
    topCandidates,
  };
}
