import type { SignalName } from "@axiom/shared";
import type { DomCandidate, PageContext } from "./base.js";

export const BASE_WEIGHTS: Record<
  Exclude<SignalName, "affordance" | "index">,
  number
> = {
  semantics: 0.45,
  context: 0.33,
  structure: 0.22,
};

export type WeightedScores = Record<
  Exclude<SignalName, "affordance" | "index">,
  number
>;

// Mixture-of-Experts weighting: page-aware dynamic adjust + post-hoc zero-signal correction (LLD-004 §5).
// Affordance gates candidates before this runs; index only tiebreaks (banding.ts) — neither is weighted.
export function computeWeights(
  page: PageContext,
  allScores: WeightedScores[],
): WeightedScores {
  const w = { ...BASE_WEIGHTS };

  if (page.iconRatio > 0.5) w.structure += 0.15;
  if (page.textDensity > 0.6) w.semantics += 0.1;
  if (page.hasForm || page.hasModal) w.context += 0.1;

  for (const key of Object.keys(w) as (keyof WeightedScores)[]) {
    const allZero = allScores.every((s) => s[key] === 0);
    if (allZero) w[key] = 0;
  }

  const total = w.semantics + w.context + w.structure;
  if (total === 0) return { semantics: 0, context: 0, structure: 0 };
  return {
    semantics: w.semantics / total,
    context: w.context / total,
    structure: w.structure / total,
  };
}

export function finalScore(
  scores: WeightedScores,
  weights: WeightedScores,
): number {
  return (
    scores.semantics * weights.semantics +
    scores.context * weights.context +
    scores.structure * weights.structure
  );
}

export function characterizePage(candidates: DomCandidate[]): PageContext {
  const withText = candidates.filter(
    (c) => c.label && c.label.trim().length > 0,
  ).length;
  const iconLike = candidates.filter(
    (c) => !c.label || c.label.trim().length === 0,
  ).length;
  return {
    textDensity: candidates.length ? withText / candidates.length : 0,
    iconRatio: candidates.length ? iconLike / candidates.length : 0,
    hasForm: candidates.some((c) => c.region === "form"),
    hasModal: candidates.some((c) => c.region === "modal"),
    repeatedStructure:
      new Set(candidates.map((c) => c.tag)).size < candidates.length / 2,
  };
}
