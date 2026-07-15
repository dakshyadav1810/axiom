# LLD-004: Multi-Signal Resolver (`core/resolver`)

**Status:** Draft
**Implements:** [ADR-002 §3](../adr/ADR-002.md), [ADR-003 §4](../adr/ADR-003.md) · **Prior art:** [DISCUSSION.md](../DISCUSSION.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md) (Candidate/Resolution/SignalScores), [LLD-007](./LLD-007-storage.md) (embedding cache)

> The differentiator. A **pure, deterministic** engine that scores live candidates against a Tier-1
> target across five signals, blends them with page-aware weights, and returns a ranked resolution with a
> confidence band. **No network, no generative LLM** — the semantic signal is a local embedding model.

---

## 1. Module shape

```
core/src/resolver/
├── index.ts              # ResolverRouter (public interface)
├── base.ts               # SignalStrategy interface
├── signals/
│   ├── semantics.ts      # local embedding + cosine
│   ├── affordance.ts     # capability filter
│   ├── context.ts        # ancestor/region/nearby-text
│   ├── structure.ts      # structural identity (was "selector")
│   └── index-signal.ts   # positional / nth-match
├── router.ts             # Mixture-of-Experts routing + dynamic weights
├── banding.ts            # score → band, margin checks, select-best
└── embeddings.ts         # EmbeddingModel (ONNX) + SQLite-cached vectors
```

## 2. Interfaces (pure)

```ts
export interface SignalStrategy {
  readonly name: SignalName;                    // "semantics" | "affordance" | ...
  score(target: Tier1Target, cand: DomCandidate, ctx: PageContext): number; // 0..1 (affordance: 0/1)
}

export interface Resolver {
  resolve(input: ResolverInput): Resolution;    // deterministic, no I/O except cached embeddings
}

export type ResolverInput = {
  target: Tier1Target;
  candidates: DomCandidate[];
  page: PageContext;                            // text density, icon ratio, has_form/modal, repeats
  generalization: Generalization;
};
```

Strategies are **deterministic and side-effect-free** (the semantics strategy reads only from the
embedding cache, which is itself a pure function of text → fixed-weight vector).

## 3. The five signals

| Signal | What it answers | Algorithm (summary) |
|---|---|---|
| **semantics** | "does this mean what the user intended?" | cosine similarity between the embedding of `target.semantics`+`label` and the embedding of the candidate's accessible text; §4 |
| **affordance** | "can it perform this action?" | hard **filter**: visible+enabled, then per-`action` capability (click/type/select/…). Fails → candidate dropped |
| **context** | "is it in the right place?" | ancestor chain (≤5) + region (form/modal/section) match + nearby-text Jaccard; penalty for wrong neighborhood |
| **structure** | "can we identify it by what it is?" | structural identity: `testId`/`id`/attrs match, tag, role (with synonyms), stable CSS/xpath match → high; the old `selector` signal |
| **index** | "is it identified by position?" | positional/nth match vs recorded sibling index; last-resort; refuses to guess on ambiguous repeats |

**Design note (ADR-003):** `semantics` is now embedding-based, **not** `rapidfuzz`. Fuzzy string matching
is removed. `structure` is the old code's `selector` signal, renamed to the product vocabulary.

## 4. Semantic signal via local embeddings (`semantics.ts` + `embeddings.ts`)

- **Model:** a fixed-weight ONNX sentence-embedding model (default `Xenova/all-MiniLM-L6-v2` via
  transformers.js; fastembed acceptable) loaded once in-process. Deterministic output; no network call
  after weights are present. This keeps the runtime LLM-free (ADR-001) while giving true semantic
  similarity instead of lexical overlap.
- **Scoring:** `score = max(cosine(embed(targetText_i), embed(candText)))` over the target's
  `semantics[]`+`label`, where `candText` is the candidate's accessible name (visible text / aria-label /
  placeholder / label-for). Cosine ∈ [-1,1] is clamped/rescaled to [0,1].
- **Caching:** every text→vector is cached in SQLite keyed by `sha256(model + text)` (LLD-007). Repeated
  grounding/runs reuse vectors, so the model cost is paid once per unique string.
- **No text → bypass:** icon-only candidates get semantics `0` (they must win on structure/affordance).

## 5. Router — Mixture of Experts + dynamic weights (`router.ts`)

Ported from the tuned ladder in DISCUSSION.md (re-earned via golden cases, §8):

1. **Affordance filter first** — drop candidates that can't perform the action. Affordance is a **pure
   gate**, not a scored signal: every surviving candidate has already passed it, so it carries **no
   weight** (weighting a constant `1` would add a fixed offset to every candidate and silently shift the
   effective band thresholds).
2. **Characterize the page** — text density, icon ratio, `has_form`/`has_modal`, repeated structure.
3. **Base weights:** `{ semantics: 0.45, context: 0.33, structure: 0.22 }` — they sum to `1.0`. **Index
   is not weighted** (it's a tiebreak); **affordance is not weighted** (it's the gate in step 1).
4. **Dynamic adjust:** icon-heavy → boost `structure`; text-heavy → boost `semantics`; form/modal → boost
   `context`. Any signal with no usable data for this target is zeroed; weights renormalize to 1.
5. **Post-hoc correction:** a signal that scored 0 across *all* candidates is zeroed and weights
   renormalize (empty voters can't dilute real signal).
6. **Final score:** `Σ weight_s · score_s` per candidate over the three weighted signals; sort desc.

```ts
finalScore(c) = semantics·wS + context·wC + structure·wStr    // affordance gates in step 1; index tiebreaks
```

## 6. Banding & select-best (`banding.ts`)

- **Thresholds (ADR-002):** `high` iff `score ≥ config.bands.high (0.7)`; `medium` iff `≥ bands.medium
  (0.5)`; else `low`. (Note: the reference Python used 0.78 — this design adopts ADR-002's 0.7.)
- **Margin:** the winner must lead the runner-up by `≥ CONFIDENCE_MARGIN (0.15)`; within margin, apply
  deterministic tiebreakers (recorded/durable anchor → bbox proximity → sibling index → nearby-text →
  DOM order). Persistent ambiguity → downgrade band (drives `ungrounded`/`stale`).
- **Generalization** modulates strictness across the four `Generalization` enum values (LLD-001 §1):
  `same_element` (strictest) requires the full margin; `any_matching` requires a reduced margin;
  `flexible` and `aggressive` accept the best candidate above threshold without a margin check.
- **Output:** `Resolution` (LLD-001 §5) — status, confidence, band, `selected`, `candidates[]` (grounding
  adds the `cachedSelector`).

## 7. What the resolver never does

- No network, no generative model, no file/DB writes (except reading the embedding cache).
- No Playwright / DOM access — it consumes the serialized `DomCandidate`s normalize produced (LLD-003).
- No "pick something anyway" — genuine ambiguity or absence yields a low band, which upstream turns into
  author review, never a guess.

## 8. Testing — golden cases (Vitest)

The tuned behavior in DISCUSSION.md is locked with **golden-case tests**: fixtures of
`(target, candidates[])` → expected `(selected, band)`, covering the documented pass/heal/fail scenarios
(unique semantic match, durable anchor, icon-only → low, ambiguous repeats → margin fail, navigation
guard). These are the parity gate against the retired Python resolver and guard future weight tuning.

## 9. Open knobs (untuned, per ADR-002)

Band thresholds (0.5/0.7), the margin (0.15), base weights, and the embedding model are all config-driven
and **untuned against real corpora**. The optimization objective is **minimizing false positives**
(locating the wrong element confidently); thresholds move as benchmark data arrives.

One known interaction to tune with the corpus: dynamic re-weighting + renormalization (§5) makes the final
score's composition page-dependent, while the bands (§6) are absolute cutoffs. A score of `0.7` assembled
from different weight mixes is not strictly the same evidence, so band boundaries should be validated
per-page-archetype, not assumed globally stable. The golden cases (§8) pin current behavior but do not by
themselves certify the thresholds.
