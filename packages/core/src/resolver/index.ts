import type { AxiomConfig, Candidate, Resolution } from "@axiom/shared";
import { selectBest } from "./banding.js";
import type { DomCandidate, ResolverInput } from "./base.js";
import type { CachedEmbedder } from "./embeddings.js";
import { type WeightedScores, computeWeights, finalScore } from "./router.js";
import { AffordanceSignal } from "./signals/affordance.js";
import { ContextSignal } from "./signals/context.js";
import { IndexSignal } from "./signals/index-signal.js";
import { SemanticsSignal } from "./signals/semantics.js";
import { StructureSignal } from "./signals/structure.js";

export interface Resolver {
  resolve(input: ResolverInput): Promise<Resolution>;
}

// Pure (given the embedding cache): no network, no generative LLM, no DOM access — LLD-004 §7.
export class MultiSignalResolver implements Resolver {
  private affordance = new AffordanceSignal();
  private context = new ContextSignal();
  private structure = new StructureSignal();
  private index = new IndexSignal();
  private semantics: SemanticsSignal;

  constructor(
    embedder: CachedEmbedder,
    private bands: AxiomConfig["bands"],
  ) {
    this.semantics = new SemanticsSignal(embedder);
  }

  async resolve(input: ResolverInput): Promise<Resolution> {
    const { target, candidates, page, generalization } = input;

    const survivors = candidates.filter(
      (c) => this.affordance.score(target, c, page) === 1,
    );
    if (survivors.length === 0) {
      return {
        status: "ungrounded",
        confidence: 0,
        band: "low",
        selected: null,
        cachedSelector: null,
        candidates: [],
      };
    }

    const rawScores: WeightedScores[] = [];
    const semanticsScores: number[] = [];
    const contextScores: number[] = [];
    const structureScores: number[] = [];
    const indexScores: number[] = [];

    for (const c of survivors) {
      const [sem, ctx, struct] = await Promise.all([
        this.semantics.score(target, c, page),
        Promise.resolve(this.context.score(target, c, page)),
        Promise.resolve(this.structure.score(target, c, page)),
      ]);
      semanticsScores.push(sem);
      contextScores.push(ctx);
      structureScores.push(struct);
      indexScores.push(this.index.score(target, c, page));
      rawScores.push({ semantics: sem, context: ctx, structure: struct });
    }

    const weights = computeWeights(page, rawScores);

    const scored = survivors.map((c, i) => ({
      candidate: c,
      score: finalScore(rawScores[i], weights),
    }));
    const { winner, band, ambiguous } = selectBest(
      scored,
      generalization,
      this.bands,
    );

    const candidatesOut: Candidate[] = survivors.map((c, i) => ({
      id: c.id,
      selector: c.selector,
      label: c.label,
      role: c.role,
      boundingBox: c.boundingBox,
      anchors: {
        testId: c.testId,
        attributes: c.attributes ?? {},
        xpath: c.xpath,
        contextPath: c.contextPath ?? [],
        siblingIndex: c.siblingIndex,
        nearbyText: c.nearbyText,
      },
      signals: {
        semantics: semanticsScores[i],
        affordance: 1,
        context: contextScores[i],
        structure: structureScores[i],
        index: indexScores[i],
      },
      score: scored[i].score,
      band:
        scored[i].score >= this.bands.high
          ? "high"
          : scored[i].score >= this.bands.medium
            ? "medium"
            : "low",
    }));
    candidatesOut.sort((a, b) => b.score - a.score);

    if (!winner || ambiguous) {
      return {
        status: "ungrounded",
        confidence: winner?.score ?? 0,
        band,
        selected: null,
        cachedSelector: null,
        candidates: candidatesOut,
      };
    }

    return {
      status: band === "low" ? "ungrounded" : "grounded",
      confidence: winner.score,
      band,
      selected: winner.candidate.id,
      cachedSelector: null, // grounding's gate.ts fills this in from the winner's anchors
      candidates: candidatesOut,
    };
  }
}
