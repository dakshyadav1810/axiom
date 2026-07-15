import type { GroundedTest, GroundedUiStep } from "@axiom/shared";
import type { Locator, Page } from "playwright";
import type { CacheStore } from "../cache/index.js";
import { extractCandidates } from "../grounding/candidate.js";
import { computeDomHash } from "../grounding/dom-hash.js";
import type { HealingService } from "../healing/index.js";

export interface LocateResult {
  locator: Locator | null;
  source: "cached" | "resolver" | "none";
}

async function isUniqueVisible(locator: Locator): Promise<boolean> {
  const count = await locator.count();
  if (count !== 1) return false;
  return locator.isVisible().catch(() => false);
}

// Ladder: selector cache (by domHash) -> grounded-artifact selector -> runtime heal -> stale (LLD-005 §4).
export async function locate(
  test: GroundedTest,
  step: GroundedUiStep,
  page: Page,
  cache: CacheStore,
  healing: HealingService,
): Promise<LocateResult> {
  const domCandidates = await extractCandidates(page);
  const domHash = computeDomHash(domCandidates);
  const testId = test.flow.id;

  const hit = cache.getSelector(testId, step.id, domHash);
  if (hit && (await isUniqueVisible(page.locator(hit.cachedSelector)))) {
    return { locator: page.locator(hit.cachedSelector), source: "cached" };
  }

  const seed = step.target?.resolution?.cachedSelector;
  if (seed && (await isUniqueVisible(page.locator(seed)))) {
    cache.putSelector({
      testId,
      stepId: step.id,
      domHash,
      cachedSelector: seed,
      band: step.target!.resolution!.band,
    });
    return { locator: page.locator(seed), source: "cached" };
  }

  const outcome = await healing.runtimeHeal(test, step.id, page, seed ?? null);
  if (outcome.status === "healed") {
    return {
      locator: page.locator(outcome.cachedSelector),
      source: "resolver",
    };
  }
  return { locator: null, source: "none" }; // -> STALE (SPEC-003 §7)
}
