import type { Tier1Target } from "@axiom/shared";
import type { DomCandidate, PageContext, SignalStrategy } from "../base.js";

function jaccard(a: string, b: string): number {
  const setA = new Set(a.toLowerCase().split(/\s+/).filter(Boolean));
  const setB = new Set(b.toLowerCase().split(/\s+/).filter(Boolean));
  if (setA.size === 0 || setB.size === 0) return 0;
  let inter = 0;
  for (const w of setA) if (setB.has(w)) inter++;
  const union = setA.size + setB.size - inter;
  return union === 0 ? 0 : inter / union;
}

// "is it in the right place?" — ancestor chain + region + nearby-text Jaccard (LLD-004 §3)
export class ContextSignal implements SignalStrategy {
  readonly name = "context" as const;

  score(target: Tier1Target, cand: DomCandidate, ctx: PageContext): number {
    let score = 0.5; // neutral prior when there's no strong contextual evidence either way
    if (ctx.hasForm && cand.region === "form") score += 0.2;
    if (ctx.hasModal && cand.region === "modal") score += 0.2;
    if (cand.nearbyText) {
      const textMatch = Math.max(
        jaccard(cand.nearbyText, target.label),
        jaccard(cand.nearbyText, target.intent),
      );
      score += textMatch * 0.3;
    }
    return Math.min(1, score);
  }
}
