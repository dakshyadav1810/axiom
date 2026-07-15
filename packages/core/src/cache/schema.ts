import { blob, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

export const resolutionCache = sqliteTable("resolution_cache", {
  testId: text("test_id").notNull(),
  stepId: text("step_id").notNull(),
  domHash: text("dom_hash").notNull(),
  cachedSelector: text("cached_selector").notNull(),
  band: text("band").notNull(),
  groundedAt: text("grounded_at").notNull(),
});

export const embeddings = sqliteTable("embeddings", {
  hash: text("hash").primaryKey(), // sha256(model+text)
  model: text("model").notNull(),
  vector: blob("vector", { mode: "buffer" }).notNull(),
});

export const runs = sqliteTable("runs", {
  runId: text("run_id").primaryKey(),
  testId: text("test_id").notNull(),
  status: text("status").notNull(),
  needsReview: integer("needs_review", { mode: "boolean" })
    .notNull()
    .default(false),
  startedAt: text("started_at").notNull(),
  finishedAt: text("finished_at").notNull(),
});

export const stepResults = sqliteTable("step_results", {
  runId: text("run_id").notNull(),
  stepId: text("step_id").notNull(),
  status: text("status").notNull(),
  selectionSource: text("selection_source"),
  band: text("band"),
  durationMs: integer("duration_ms").notNull(),
  screenshotPath: text("screenshot_path"),
});

export const healAudit = sqliteTable("heal_audit", {
  testId: text("test_id").notNull(),
  stepId: text("step_id").notNull(),
  event: text("event").notNull(), // "healed" | "stale"
  fromSel: text("from_sel"),
  toSel: text("to_sel"),
  band: text("band"),
  reason: text("reason"),
  at: text("at").notNull(),
});

export const reviewQueue = sqliteTable("review_queue", {
  testId: text("test_id").notNull(),
  stepId: text("step_id").notNull(),
  url: text("url").notNull(),
  screenshotPath: text("screenshot_path"),
  candidatesJson: text("candidates_json"),
  open: integer("open", { mode: "boolean" }).notNull().default(true),
});
