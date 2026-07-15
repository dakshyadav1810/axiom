import type { Tier1Target } from "@axiom/shared";
import type { DomCandidate, PageContext, SignalStrategy } from "../base.js";

// "is it identified by position?" — last-resort, unweighted tiebreak (LLD-004 §3, §5)
export class IndexSignal implements SignalStrategy {
  readonly name = "index" as const;

  score(_target: Tier1Target, cand: DomCandidate, _ctx: PageContext): number {
    // No recorded expectation to compare against at scoring time (that's the tiebreak's job in
    // banding.ts) — this signal contributes a neutral value and never drives the weighted score.
    return cand.siblingIndex !== undefined ? 0.5 : 0;
  }
}
