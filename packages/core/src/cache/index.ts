import type { Band, RunReport, StepResult } from "@axiom/shared";
import { and, eq } from "drizzle-orm";
import type { DrizzleDb } from "./db.js";
import * as schema from "./schema.js";

export interface CachedSelector {
  testId: string;
  stepId: string;
  domHash: string;
  cachedSelector: string;
  band: Band;
}

export interface HealAuditEntry {
  testId: string;
  stepId: string;
  event: "healed" | "stale";
  fromSel: string | null;
  toSel: string | null;
  band?: Band;
  reason?: string;
  at: string;
}

export interface ReviewRecord {
  testId: string;
  stepId: string;
  url: string;
  screenshotPath?: string;
  candidatesJson?: string;
}

export interface CacheStore {
  getSelector(
    testId: string,
    stepId: string,
    domHash: string,
  ): CachedSelector | null;
  putSelector(e: CachedSelector): void;
  getEmbedding(hash: string): Float32Array | null;
  putEmbedding(hash: string, model: string, v: Float32Array): void;
  saveRun(report: RunReport): void;
  getRun(runId: string): RunReport | null;
  appendHeal(entry: HealAuditEntry): void;
  enqueueReview(rec: ReviewRecord): void;
  resolveReview(testId: string, stepId: string): void;
  openReviews(testId?: string): ReviewRecord[];
}

export class SqliteCacheStore implements CacheStore {
  constructor(private db: DrizzleDb) {}

  getSelector(
    testId: string,
    stepId: string,
    domHash: string,
  ): CachedSelector | null {
    const row = this.db
      .select()
      .from(schema.resolutionCache)
      .where(
        and(
          eq(schema.resolutionCache.testId, testId),
          eq(schema.resolutionCache.stepId, stepId),
          eq(schema.resolutionCache.domHash, domHash),
        ),
      )
      .get();
    if (!row) return null;
    return {
      testId: row.testId,
      stepId: row.stepId,
      domHash: row.domHash,
      cachedSelector: row.cachedSelector,
      band: row.band as Band,
    };
  }

  putSelector(e: CachedSelector): void {
    this.db
      .insert(schema.resolutionCache)
      .values({ ...e, groundedAt: new Date().toISOString() })
      .onConflictDoUpdate({
        target: [
          schema.resolutionCache.testId,
          schema.resolutionCache.stepId,
          schema.resolutionCache.domHash,
        ],
        set: {
          cachedSelector: e.cachedSelector,
          band: e.band,
          groundedAt: new Date().toISOString(),
        },
      })
      .run();
  }

  getEmbedding(hash: string): Float32Array | null {
    const row = this.db
      .select()
      .from(schema.embeddings)
      .where(eq(schema.embeddings.hash, hash))
      .get();
    if (!row) return null;
    return new Float32Array(
      row.vector.buffer,
      row.vector.byteOffset,
      row.vector.length / 4,
    );
  }

  putEmbedding(hash: string, model: string, v: Float32Array): void {
    this.db
      .insert(schema.embeddings)
      .values({
        hash,
        model,
        vector: Buffer.from(v.buffer, v.byteOffset, v.byteLength),
      })
      .onConflictDoNothing()
      .run();
  }

  saveRun(report: RunReport): void {
    this.db
      .insert(schema.runs)
      .values({
        runId: report.runId,
        testId: report.testId,
        status: report.status,
        needsReview: report.needsReview,
        startedAt: report.startedAt,
        finishedAt: report.finishedAt,
      })
      .run();
    for (const s of report.steps) {
      this.db
        .insert(schema.stepResults)
        .values({
          runId: report.runId,
          stepId: s.stepId,
          status: s.status,
          selectionSource: s.selection ?? null,
          band: s.band ?? null,
          durationMs: s.durationMs,
          screenshotPath: s.screenshot ?? null,
        })
        .run();
    }
  }

  getRun(runId: string): RunReport | null {
    const run = this.db
      .select()
      .from(schema.runs)
      .where(eq(schema.runs.runId, runId))
      .get();
    if (!run) return null;
    const steps = this.db
      .select()
      .from(schema.stepResults)
      .where(eq(schema.stepResults.runId, runId))
      .all();
    return {
      runId: run.runId,
      testId: run.testId,
      status: run.status as "passed" | "failed",
      needsReview: run.needsReview,
      startedAt: run.startedAt,
      finishedAt: run.finishedAt,
      steps: steps.map((s) => ({
        stepId: s.stepId,
        status: s.status as StepResult["status"],
        selection: (s.selectionSource ?? undefined) as StepResult["selection"],
        band: (s.band ?? undefined) as StepResult["band"],
        durationMs: s.durationMs,
        screenshot: s.screenshotPath ?? undefined,
      })),
    };
  }

  appendHeal(entry: HealAuditEntry): void {
    this.db
      .insert(schema.healAudit)
      .values({
        ...entry,
        band: entry.band ?? null,
        reason: entry.reason ?? null,
      })
      .run();
  }

  enqueueReview(rec: ReviewRecord): void {
    this.db
      .insert(schema.reviewQueue)
      .values({
        testId: rec.testId,
        stepId: rec.stepId,
        url: rec.url,
        screenshotPath: rec.screenshotPath ?? null,
        candidatesJson: rec.candidatesJson ?? null,
        open: true,
      })
      .run();
  }

  resolveReview(testId: string, stepId: string): void {
    this.db
      .update(schema.reviewQueue)
      .set({ open: false })
      .where(
        and(
          eq(schema.reviewQueue.testId, testId),
          eq(schema.reviewQueue.stepId, stepId),
        ),
      )
      .run();
  }

  openReviews(testId?: string): ReviewRecord[] {
    const rows = testId
      ? this.db
          .select()
          .from(schema.reviewQueue)
          .where(
            and(
              eq(schema.reviewQueue.testId, testId),
              eq(schema.reviewQueue.open, true),
            ),
          )
          .all()
      : this.db
          .select()
          .from(schema.reviewQueue)
          .where(eq(schema.reviewQueue.open, true))
          .all();
    return rows.map((r) => ({
      testId: r.testId,
      stepId: r.stepId,
      url: r.url,
      screenshotPath: r.screenshotPath ?? undefined,
      candidatesJson: r.candidatesJson ?? undefined,
    }));
  }
}
