import type { Generalization, Tier1Target } from "@axiom/shared";
import type { DomCandidate, ResolverInput } from "../resolver/base.js";
import { characterizePage } from "../resolver/router.js";

// Only place spec-side and DOM-side data meet — pure, keeps the resolver free of extraction details (LLD-003 §5).
export function normalize(
  target: Tier1Target,
  candidates: DomCandidate[],
  generalization: Generalization,
): ResolverInput {
  return {
    target,
    candidates,
    page: characterizePage(candidates),
    generalization,
  };
}
