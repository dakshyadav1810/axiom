import type { Tier1Target } from "@axiom/shared";
import type { DomCandidate, PageContext, SignalStrategy } from "../base.js";
import type { CachedEmbedder } from "../embeddings.js";
import { cosineSimilarity } from "../embeddings.js";

// "does this mean what the user intended?" — LLD-004 §3-4
export class SemanticsSignal implements SignalStrategy {
  readonly name = "semantics" as const;
  constructor(private embedder: CachedEmbedder) {}

  async score(
    target: Tier1Target,
    cand: DomCandidate,
    _ctx: PageContext,
  ): Promise<number> {
    const candText = cand.label?.trim();
    if (!candText) return 0; // icon-only candidates must win on structure/affordance instead

    const targetTexts = [...target.semantics, target.label];
    const candVec = await this.embedder.embed(candText);
    let best = -1;
    for (const t of targetTexts) {
      const vec = await this.embedder.embed(t);
      best = Math.max(best, cosineSimilarity(vec, candVec));
    }
    return Math.min(1, Math.max(0, (best + 1) / 2)); // clamp/rescale [-1,1] -> [0,1]
  }
}
