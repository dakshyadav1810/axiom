import type { DrizzleDb } from "./db.js";

// Migrations run on startup; schema defined once in Drizzle (schema.ts) and typed from it (LLD-007 §6).
export function migrate(db: DrizzleDb): void {
  const sqlite = (
    db as unknown as { $client: import("better-sqlite3").Database }
  ).$client;
  sqlite.exec(`
    CREATE TABLE IF NOT EXISTS resolution_cache (
      test_id TEXT NOT NULL, step_id TEXT NOT NULL, dom_hash TEXT NOT NULL,
      cached_selector TEXT NOT NULL, band TEXT NOT NULL, grounded_at TEXT NOT NULL,
      PRIMARY KEY (test_id, step_id, dom_hash)
    );
    CREATE TABLE IF NOT EXISTS embeddings (
      hash TEXT PRIMARY KEY, model TEXT NOT NULL, vector BLOB NOT NULL
    );
    CREATE TABLE IF NOT EXISTS runs (
      run_id TEXT PRIMARY KEY, test_id TEXT NOT NULL, status TEXT NOT NULL,
      needs_review INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL, finished_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS step_results (
      run_id TEXT NOT NULL, step_id TEXT NOT NULL, status TEXT NOT NULL,
      selection_source TEXT, band TEXT, duration_ms INTEGER NOT NULL, screenshot_path TEXT
    );
    CREATE TABLE IF NOT EXISTS heal_audit (
      test_id TEXT NOT NULL, step_id TEXT NOT NULL, event TEXT NOT NULL,
      from_sel TEXT, to_sel TEXT, band TEXT, reason TEXT, at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS review_queue (
      test_id TEXT NOT NULL, step_id TEXT NOT NULL, url TEXT NOT NULL,
      screenshot_path TEXT, candidates_json TEXT, open INTEGER NOT NULL DEFAULT 1
    );
  `);
}
