# LLD-007: Storage — Artifacts (JSON-in-git) + Cache (Drizzle/SQLite)

**Status:** Draft
**Implements:** [ADR-002 §3](../../ADR-002.md) (versioned vs ephemeral), [ADR-003 §3](../../ADR-003.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md) (all persisted shapes)

> Two persistence tiers with a hard boundary: **versioned JSON artifacts** in git are the source of truth;
> the **SQLite cache** (better-sqlite3 + Drizzle) holds only regenerable data. Nothing in the cache is
> ever the source of truth; deleting `cache.db` must lose nothing but speed.

---

## 1. Module shape

```
core/src/storage/           # versioned artifacts (JSON-in-git)
├── index.ts                # ArtifactStore
└── layout.ts               # on-disk paths
core/src/cache/             # ephemeral cache (SQLite)
├── index.ts                # CacheStore
├── schema.ts               # Drizzle table definitions
├── migrate.ts              # migrations
└── db.ts                   # better-sqlite3 connection
```

## 2. Tier 1 — versioned artifacts (`storage/`)

Source of truth, committed to git, human-diffable JSON validated by `shared` schemas.

```
<project>/.axiom/
├── tests/
│   └── <testId>/
│       ├── spec.json           # SpecIR (LLD-001 §4)        — authored, DOM-blind
│       ├── candidates.json     # CandidatesDoc (LLD-001 §5) — grounding output
│       └── grounded.json       # GroundedTest (LLD-001 §6)  — runnable artifact
└── axiom.config.json           # AxiomConfig (LLD-001 §7)
```

```ts
export interface ArtifactStore {
  saveSpec(spec: SpecIR): Promise<string>;                 // → testId
  saveGrounded(test: GroundedTest): Promise<void>;
  saveCandidates(doc: CandidatesDoc): Promise<void>;
  loadSpec(testId: string): Promise<SpecIR>;
  loadGrounded(testId: string): Promise<GroundedTest>;
  list(): Promise<TestSummary[]>;
}
```

All writes re-validate against the Zod schema before hitting disk (fail closed on drift).

## 3. Tier 2 — SQLite cache (`cache/`, Drizzle + better-sqlite3)

Regenerable, git-ignored (`.axiom/cache.db`). Holds the runtime fast path, embeddings, and history.

| Table | Purpose | Key columns |
|---|---|---|
| `resolution_cache` | fast-path locator per step | `test_id, step_id, dom_hash → cached_selector, band, grounded_at` |
| `embeddings` | text→vector cache for the semantic signal | `hash (sha256(model+text)) → vector (blob), model` |
| `runs` | run history | `run_id, test_id, status, started_at, finished_at` |
| `step_results` | per-step outcomes | `run_id, step_id, status, selection_source, band, duration_ms, screenshot_path` |
| `heal_audit` | heal/stale audit (LLD-006) | `test_id, step_id, event, from_sel, to_sel, band, reason, at` |
| `review_queue` | stale author-review records | `test_id, step_id, url, screenshot_path, candidates_json, open` |
| `screenshots` | artifact blobs/paths | `id, run_id, step_id, path` |

```ts
export interface CacheStore {
  getSelector(testId: string, stepId: string, domHash: string): CachedSelector | null;
  putSelector(e: CachedSelector): void;
  getEmbedding(hash: string): Float32Array | null;
  putEmbedding(hash: string, model: string, v: Float32Array): void;
  saveRun(report: RunReport): void;
  appendHeal(entry: HealAudit): void;
  enqueueReview(rec: ReviewRecord): void;  resolveReview(testId: string, stepId: string): void;
}
```

## 4. Cache keys & invalidation

- **Selector cache key = `(testId, stepId, domHash)`** — `domHash` is a stable hash of the page's
  interactive-DOM signature, so a materially changed page misses the cache and triggers a re-ground
  (runtime heal) rather than using a stale selector.
- **Embedding key = `sha256(model + text)`** — model-scoped, so swapping the embedding model invalidates
  cleanly.
- Cache entries are freely evictable; a miss simply re-derives via the resolver.

## 5. Dual backend (thin, future)

For the paid/cloud tier, `CacheStore`/`ArtifactStore` are interfaces; a Supabase-backed implementation
(`@supabase/supabase-js`) can replace SQLite/local-FS behind the same contract. Local `npx axiom` uses
SQLite + local FS by default; no cloud dependency. (Kept thin this pass.)

## 6. Boundaries & guarantees

- **Never** store a Playwright script as a primary artifact (invariant #2) — only JSON IR.
- Deleting `cache.db` loses only speed: selectors re-ground, embeddings recompute, history clears.
- Only `storage` writes versioned artifacts; grounding/execution/healing write cache via `cache`.
- Migrations run on startup; schema is defined once in Drizzle and typed from it.
