import { createHash } from "node:crypto";
import type { CacheStore } from "../cache/index.js";

export interface EmbeddingModel {
  embed(text: string): Promise<Float32Array>;
}

// Fixed-weight ONNX sentence-embedding model (transformers.js), loaded once. Deterministic;
// no network call after weights are cached locally (ADR-001/003).
export class TransformersEmbeddingModel implements EmbeddingModel {
  private pipe: unknown | null = null;

  constructor(private modelId: string) {}

  private async load() {
    if (this.pipe) return this.pipe;
    const { pipeline } = await import("@huggingface/transformers");
    this.pipe = await pipeline("feature-extraction", this.modelId);
    return this.pipe;
  }

  async embed(text: string): Promise<Float32Array> {
    const pipe = (await this.load()) as (
      text: string,
      opts: { pooling: "mean"; normalize: boolean },
    ) => Promise<{ data: Float32Array }>;
    const out = await pipe(text, { pooling: "mean", normalize: true });
    return out.data;
  }
}

export function embeddingCacheKey(model: string, text: string): string {
  return createHash("sha256").update(`${model}:${text}`).digest("hex");
}

export function cosineSimilarity(a: Float32Array, b: Float32Array): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  if (na === 0 || nb === 0) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

// Cache-through embedding lookup, keyed by sha256(model+text) — LLD-004 §4, LLD-007 §4.
export class CachedEmbedder {
  constructor(
    private model: EmbeddingModel,
    private modelId: string,
    private cache: CacheStore,
  ) {}

  async embed(text: string): Promise<Float32Array> {
    const key = embeddingCacheKey(this.modelId, text);
    const cached = this.cache.getEmbedding(key);
    if (cached) return cached;
    const vector = await this.model.embed(text);
    this.cache.putEmbedding(key, this.modelId, vector);
    return vector;
  }
}
