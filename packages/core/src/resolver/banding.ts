import type { AxiomConfig, Band, Generalization } from "@axiom/shared";
import type { DomCandidate } from "./base.js";

export const CONFIDENCE_MARGIN = 0.15;

export function toBand(score: number, bands: AxiomConfig["bands"]): Band {
  if (score >= bands.high) return "high";
  if (score >= bands.medium) return "medium";
  return "low";
}

export interface Scored {
  candidate: DomCandidate;
  score: number;
}

// Winner must lead the runner-up by CONFIDENCE_MARGIN under strict generalizations; otherwise
// deterministic tiebreakers apply. Persistent ambiguity downgrades the band rather than guessing (LLD-004 §6).
export function selectBest(
  scored: Scored[],
  generalization: Generalization,
  bands: AxiomConfig["bands"],
): { winner: Scored | null; band: Band; ambiguous: boolean } {
  if (scored.length === 0)
    return { winner: null, band: "low", ambiguous: false };

  const sorted = [...scored].sort((a, b) => b.score - a.score);
  const top = sorted[0];
  const runnerUp = sorted[1];
  const requiresMargin =
    generalization === "same_element" || generalization === "any_matching";
  const margin =
    generalization === "same_element"
      ? CONFIDENCE_MARGIN
      : CONFIDENCE_MARGIN / 2;

  let band = toBand(top.score, bands);
  let ambiguous = false;

  if (requiresMargin && runnerUp && top.score - runnerUp.score < margin) {
    const tiebreakWinner = tiebreak(
      sorted.filter((s) => top.score - s.score < margin),
    );
    if (tiebreakWinner) {
      return {
        winner: tiebreakWinner,
        band: toBand(tiebreakWinner.score, bands),
        ambiguous: false,
      };
    }
    ambiguous = true;
    band = band === "high" ? "medium" : "low"; // downgrade rather than guess
  }

  return { winner: top, band, ambiguous };
}

// Deterministic cascade: durable anchor -> bbox proximity -> sibling index -> nearby-text -> DOM order.
function tiebreak(tied: Scored[]): Scored | null {
  const withTestId = tied.find((s) => s.candidate.testId);
  if (withTestId) return withTestId;
  const withSiblingIndex = [...tied].sort(
    (a, b) =>
      (a.candidate.siblingIndex ?? 99) - (b.candidate.siblingIndex ?? 99),
  );
  if (withSiblingIndex[0]?.candidate.siblingIndex !== undefined)
    return withSiblingIndex[0];
  return null; // genuinely ambiguous — caller downgrades the band
}
