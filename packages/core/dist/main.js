var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// src/server/app.ts
import path from "path";
import fastifyStatic from "@fastify/static";
import fastifyWebsocket from "@fastify/websocket";
import Fastify from "fastify";
import {
  serializerCompiler,
  validatorCompiler
} from "fastify-type-provider-zod";

// src/server/routes.ts
import { randomUUID } from "crypto";
import { MaintainRequest, RunRequest } from "@axiom/shared";
function apiError(code, message) {
  return { error: { code, message } };
}
async function registerRoutes(app2, c, hub) {
  app2.get("/health", async () => ({ ok: true, version: "0.1.0" }));
  app2.post("/tests", async (req, reply) => {
    try {
      const spec = await c.authoring.submit(req.body);
      const testId = await c.store.saveSpec(spec);
      return { testId, spec };
    } catch (e) {
      reply.code(400);
      return apiError("validation", String(e));
    }
  });
  app2.get("/tests", async () => c.store.list());
  app2.get("/tests/:id", async (req, reply) => {
    const { id } = req.params;
    try {
      return await c.store.loadGrounded(id);
    } catch {
      try {
        return await c.store.loadSpec(id);
      } catch {
        reply.code(404);
        return apiError("not_found", `test ${id} not found`);
      }
    }
  });
  app2.delete("/tests/:id", async (req) => {
    const { id } = req.params;
    await c.store.delete(id);
    return { ok: true };
  });
  app2.post("/tests/:id/ground", async (req, reply) => {
    const { id } = req.params;
    const spec = await c.store.loadSpec(id);
    const outcome = await c.grounding.ground(spec, {});
    await c.store.saveCandidates(id, outcome.candidates);
    await c.store.saveGrounded(id, outcome.grounded);
    if (outcome.stoppedAt) reply.code(200);
    return outcome;
  });
  app2.get("/tests/:id/repair", async (req) => {
    const { id } = req.params;
    return c.healing.buildRepairPayload(id);
  });
  app2.post("/tests/:id/maintain", async (req) => {
    const { id } = req.params;
    const { stepIds, spec } = MaintainRequest.parse(req.body);
    const result = await c.healing.maintain(id, stepIds, spec);
    await c.store.saveGrounded(id, result.after);
    return result;
  });
  app2.post("/runs", async (req) => {
    const { testId, vars } = RunRequest.parse(req.body);
    const test = await c.store.loadGrounded(testId);
    const runId = randomUUID();
    c.runner.run(test, { vars, runId, emit: (m) => hub.emit(`run:${runId}`, m) }).catch((e) => req.log.error(e));
    return { runId };
  });
  app2.get("/runs/:id", async (req, reply) => {
    const { id } = req.params;
    const report = c.cache.getRun(id);
    if (!report) {
      reply.code(404);
      return apiError("not_found", `run ${id} not found`);
    }
    return report;
  });
  app2.get("/kdg", async (req) => {
    const { entry } = req.query;
    return c.kdg.build(entry ?? "");
  });
  app2.get("/kdg/delta", async () => ({ changed: [] }));
}

// src/server/ws-hub.ts
var WsHub = class {
  subs = /* @__PURE__ */ new Map();
  subscribe(key, socket) {
    if (!this.subs.has(key)) this.subs.set(key, /* @__PURE__ */ new Set());
    this.subs.get(key).add(socket);
  }
  unsubscribe(key, socket) {
    this.subs.get(key)?.delete(socket);
  }
  emit(key, message) {
    for (const socket of this.subs.get(key) ?? []) {
      socket.send(JSON.stringify(message));
    }
  }
};

// src/server/ws-routes.ts
async function registerWsRoutes(app2, hub) {
  app2.get("/ws/runs/:id", { websocket: true }, (socket, req) => {
    const { id } = req.params;
    const key = `run:${id}`;
    hub.subscribe(key, socket);
    socket.on("close", () => hub.unsubscribe(key, socket));
  });
  app2.get("/ws/ground/:id", { websocket: true }, (socket, req) => {
    const { id } = req.params;
    const key = `ground:${id}`;
    hub.subscribe(key, socket);
    socket.on("close", () => hub.unsubscribe(key, socket));
  });
}

// src/server/app.ts
async function buildApp(config2, container2) {
  const app2 = Fastify({ logger: true }).withTypeProvider();
  app2.setValidatorCompiler(validatorCompiler);
  app2.setSerializerCompiler(serializerCompiler);
  await app2.register(fastifyWebsocket);
  await app2.register(fastifyStatic, {
    root: path.join(import.meta.dirname, "..", "static"),
    prefix: "/"
  });
  const hub = new WsHub();
  await registerRoutes(app2, container2, hub);
  await registerWsRoutes(app2, hub);
  app2.setErrorHandler((err, _req, reply) => {
    reply.code(err.statusCode ?? 500).send({ error: { code: "validation", message: err.message } });
  });
  return app2;
}

// src/server/config.ts
import fs from "fs";
import { AxiomConfig } from "@axiom/shared";
function loadConfig() {
  let fileConfig = {};
  try {
    fileConfig = JSON.parse(fs.readFileSync("axiom.config.json", "utf-8"));
  } catch {
  }
  const envConfig = process.env.AXIOM_PORT ? { port: Number(process.env.AXIOM_PORT) } : {};
  return AxiomConfig.parse({ ...fileConfig, ...envConfig });
}

// src/authoring/index.ts
import { lintSpec, SpecIR } from "@axiom/shared";

// src/authoring/emitter.ts
function normalizeLlmOutput(raw) {
  if (typeof raw !== "object" || raw === null) return raw;
  const toCamel = (s) => s.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
  const walk = (v) => {
    if (Array.isArray(v)) return v.map(walk);
    if (typeof v === "object" && v !== null) {
      return Object.fromEntries(
        Object.entries(v).map(([k, val]) => [
          toCamel(k),
          walk(val)
        ])
      );
    }
    return v;
  };
  return walk(raw);
}

// src/authoring/index.ts
var AuthoringError = class extends Error {
};
var CoreAuthoringService = class {
  constructor(kdg) {
    this.kdg = kdg;
  }
  kdg;
  async context(entryUrl) {
    return this.kdg.build(entryUrl);
  }
  async submit(spec) {
    const parsed = SpecIR.parse(normalizeLlmOutput(spec));
    const lint = lintSpec(parsed);
    if (!lint.ok) throw new AuthoringError(`spec failed lint: ${lint.errors.join("; ")}`);
    return parsed;
  }
};

// src/authoring/kdg-context.ts
var EmptyKdgContextProvider = class {
  async build(_entryUrl) {
    return { routes: [], conditionals: [] };
  }
};

// src/cache/db.ts
import fs2 from "fs";
import path2 from "path";
import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";

// src/cache/schema.ts
var schema_exports = {};
__export(schema_exports, {
  embeddings: () => embeddings,
  healAudit: () => healAudit,
  resolutionCache: () => resolutionCache,
  reviewQueue: () => reviewQueue,
  runs: () => runs,
  stepResults: () => stepResults
});
import { blob, integer, sqliteTable, text } from "drizzle-orm/sqlite-core";
var resolutionCache = sqliteTable("resolution_cache", {
  testId: text("test_id").notNull(),
  stepId: text("step_id").notNull(),
  domHash: text("dom_hash").notNull(),
  cachedSelector: text("cached_selector").notNull(),
  band: text("band").notNull(),
  groundedAt: text("grounded_at").notNull()
});
var embeddings = sqliteTable("embeddings", {
  hash: text("hash").primaryKey(),
  // sha256(model+text)
  model: text("model").notNull(),
  vector: blob("vector", { mode: "buffer" }).notNull()
});
var runs = sqliteTable("runs", {
  runId: text("run_id").primaryKey(),
  testId: text("test_id").notNull(),
  status: text("status").notNull(),
  needsReview: integer("needs_review", { mode: "boolean" }).notNull().default(false),
  startedAt: text("started_at").notNull(),
  finishedAt: text("finished_at").notNull()
});
var stepResults = sqliteTable("step_results", {
  runId: text("run_id").notNull(),
  stepId: text("step_id").notNull(),
  status: text("status").notNull(),
  selectionSource: text("selection_source"),
  band: text("band"),
  durationMs: integer("duration_ms").notNull(),
  screenshotPath: text("screenshot_path")
});
var healAudit = sqliteTable("heal_audit", {
  testId: text("test_id").notNull(),
  stepId: text("step_id").notNull(),
  event: text("event").notNull(),
  // "healed" | "stale"
  fromSel: text("from_sel"),
  toSel: text("to_sel"),
  band: text("band"),
  reason: text("reason"),
  at: text("at").notNull()
});
var reviewQueue = sqliteTable("review_queue", {
  testId: text("test_id").notNull(),
  stepId: text("step_id").notNull(),
  url: text("url").notNull(),
  screenshotPath: text("screenshot_path"),
  candidatesJson: text("candidates_json"),
  open: integer("open", { mode: "boolean" }).notNull().default(true)
});

// src/cache/db.ts
function openDb(dbPath) {
  fs2.mkdirSync(path2.dirname(dbPath), { recursive: true });
  const sqlite = new Database(dbPath);
  sqlite.pragma("journal_mode = WAL");
  return drizzle(sqlite, { schema: schema_exports });
}

// src/cache/index.ts
import { and, eq } from "drizzle-orm";
var SqliteCacheStore = class {
  constructor(db) {
    this.db = db;
  }
  db;
  getSelector(testId, stepId, domHash) {
    const row = this.db.select().from(resolutionCache).where(
      and(
        eq(resolutionCache.testId, testId),
        eq(resolutionCache.stepId, stepId),
        eq(resolutionCache.domHash, domHash)
      )
    ).get();
    if (!row) return null;
    return {
      testId: row.testId,
      stepId: row.stepId,
      domHash: row.domHash,
      cachedSelector: row.cachedSelector,
      band: row.band
    };
  }
  putSelector(e) {
    this.db.insert(resolutionCache).values({ ...e, groundedAt: (/* @__PURE__ */ new Date()).toISOString() }).onConflictDoUpdate({
      target: [
        resolutionCache.testId,
        resolutionCache.stepId,
        resolutionCache.domHash
      ],
      set: {
        cachedSelector: e.cachedSelector,
        band: e.band,
        groundedAt: (/* @__PURE__ */ new Date()).toISOString()
      }
    }).run();
  }
  getEmbedding(hash) {
    const row = this.db.select().from(embeddings).where(eq(embeddings.hash, hash)).get();
    if (!row) return null;
    return new Float32Array(
      row.vector.buffer,
      row.vector.byteOffset,
      row.vector.length / 4
    );
  }
  putEmbedding(hash, model, v) {
    this.db.insert(embeddings).values({
      hash,
      model,
      vector: Buffer.from(v.buffer, v.byteOffset, v.byteLength)
    }).onConflictDoNothing().run();
  }
  saveRun(report) {
    this.db.insert(runs).values({
      runId: report.runId,
      testId: report.testId,
      status: report.status,
      needsReview: report.needsReview,
      startedAt: report.startedAt,
      finishedAt: report.finishedAt
    }).run();
    for (const s of report.steps) {
      this.db.insert(stepResults).values({
        runId: report.runId,
        stepId: s.stepId,
        status: s.status,
        selectionSource: s.selection ?? null,
        band: s.band ?? null,
        durationMs: s.durationMs,
        screenshotPath: s.screenshot ?? null
      }).run();
    }
  }
  getRun(runId) {
    const run = this.db.select().from(runs).where(eq(runs.runId, runId)).get();
    if (!run) return null;
    const steps = this.db.select().from(stepResults).where(eq(stepResults.runId, runId)).all();
    return {
      runId: run.runId,
      testId: run.testId,
      status: run.status,
      needsReview: run.needsReview,
      startedAt: run.startedAt,
      finishedAt: run.finishedAt,
      steps: steps.map((s) => ({
        stepId: s.stepId,
        status: s.status,
        selection: s.selectionSource ?? void 0,
        band: s.band ?? void 0,
        durationMs: s.durationMs,
        screenshot: s.screenshotPath ?? void 0
      }))
    };
  }
  appendHeal(entry) {
    this.db.insert(healAudit).values({
      ...entry,
      band: entry.band ?? null,
      reason: entry.reason ?? null
    }).run();
  }
  enqueueReview(rec) {
    this.db.insert(reviewQueue).values({
      testId: rec.testId,
      stepId: rec.stepId,
      url: rec.url,
      screenshotPath: rec.screenshotPath ?? null,
      candidatesJson: rec.candidatesJson ?? null,
      open: true
    }).run();
  }
  resolveReview(testId, stepId) {
    this.db.update(reviewQueue).set({ open: false }).where(
      and(
        eq(reviewQueue.testId, testId),
        eq(reviewQueue.stepId, stepId)
      )
    ).run();
  }
  openReviews(testId) {
    const rows = testId ? this.db.select().from(reviewQueue).where(
      and(
        eq(reviewQueue.testId, testId),
        eq(reviewQueue.open, true)
      )
    ).all() : this.db.select().from(reviewQueue).where(eq(reviewQueue.open, true)).all();
    return rows.map((r) => ({
      testId: r.testId,
      stepId: r.stepId,
      url: r.url,
      screenshotPath: r.screenshotPath ?? void 0,
      candidatesJson: r.candidatesJson ?? void 0
    }));
  }
};

// src/cache/migrate.ts
function migrate(db) {
  const sqlite = db.$client;
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

// src/execution/dispatcher.ts
import { randomUUID as randomUUID2 } from "crypto";

// src/execution/assert.ts
function interpolate(s, vars) {
  return s.replace(/\$\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}
async function evaluateAssertion(a, ctx) {
  switch (a.type) {
    case "urlContains":
      return ok(
        ctx.page ? ctx.page.url().includes(interpolate(a.expected, ctx.vars)) : false
      );
    case "textContains": {
      const text2 = await ctx.page?.textContent("body");
      return ok(!!text2?.includes(interpolate(a.expected, ctx.vars)));
    }
    case "value": {
      const val = await ctx.page?.locator(":focus").inputValue().catch(() => "");
      return ok(val === interpolate(a.expected, ctx.vars));
    }
    case "elementVisible":
      return ok(
        !!await ctx.page?.getByRole(a.target.role, { name: a.target.label }).isVisible().catch(() => false)
      );
    case "elementAbsent":
      return ok(
        !await ctx.page?.getByRole(a.target.role, { name: a.target.label }).isVisible().catch(() => false)
      );
    case "apiStatus":
      return ok(ctx.apiResponse?.status === a.expected);
    case "apiBody":
      return ok(
        JSON.stringify(getPath(ctx.apiResponse?.body, a.path)) === JSON.stringify(a.expected)
      );
    case "dbRow":
      return ok(JSON.stringify(ctx.dbRow) === JSON.stringify(a.expected));
  }
}
async function evaluateExpectedOutcome(o, ctx) {
  switch (o.type) {
    case "navigation":
    case "url_change":
      return ok(
        ctx.page.url() !== ctx.urlBefore && (o.type === "navigation" || ctx.page.url().includes(o.value))
      );
    case "element_appears":
      return ok(
        await ctx.page.locator(o.value).isVisible().catch(() => false)
      );
    case "text_contains": {
      const text2 = await ctx.page.textContent("body");
      return ok(!!text2?.includes(interpolate(o.value, ctx.vars)));
    }
    case "field_contains": {
      const val = await ctx.page.locator(":focus").inputValue().catch(() => "");
      return ok(val.includes(interpolate(o.value, ctx.vars)));
    }
  }
}
function ok(b) {
  return b ? { ok: true } : { ok: false, reason: "assertion returned false" };
}
function getPath(obj, path4) {
  return path4.split(".").reduce((o, k) => o?.[k], obj);
}

// src/execution/adapters/api.ts
function interpolate2(s, vars) {
  return s.replace(/\$\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}
var ApiAdapter = class {
  kind = "api";
  async execute(step, ctx) {
    const start = Date.now();
    const url = interpolate2(step.request.url, ctx.vars);
    const res = await fetch(url, {
      method: step.request.method,
      headers: step.request.headers,
      body: step.request.body ? JSON.stringify(step.request.body) : void 0
    });
    const body = await res.json().catch(() => void 0);
    for (const a of step.assertions) {
      const outcome = await evaluateAssertion(a, {
        apiResponse: { status: res.status, body },
        vars: ctx.vars
      });
      if (!outcome.ok) {
        return {
          stepId: step.id,
          status: "failed",
          failure: {
            reason: "ASSERTION_FAILED",
            message: outcome.reason ?? ""
          },
          durationMs: Date.now() - start
        };
      }
    }
    return {
      stepId: step.id,
      status: "passed",
      durationMs: Date.now() - start
    };
  }
};

// src/execution/adapters/db.ts
var DbAdapter = class {
  kind = "db";
  async execute(step, ctx) {
    const start = Date.now();
    if (!ctx.dbQuery) {
      return {
        stepId: step.id,
        status: "failed",
        failure: {
          reason: "NO_DB_CONFIGURED",
          message: "config.db.url is not set"
        },
        durationMs: Date.now() - start
      };
    }
    const row = await ctx.dbQuery(step.query);
    for (const a of step.assertions) {
      const outcome = await evaluateAssertion(a, {
        dbRow: row,
        vars: ctx.vars
      });
      if (!outcome.ok) {
        return {
          stepId: step.id,
          status: "failed",
          failure: {
            reason: "ASSERTION_FAILED",
            message: outcome.reason ?? ""
          },
          durationMs: Date.now() - start
        };
      }
    }
    return {
      stepId: step.id,
      status: "passed",
      durationMs: Date.now() - start
    };
  }
};

// src/execution/act.ts
function interpolate3(value, vars) {
  if (!value) return "";
  return value.replace(/\$\{(\w+)\}/g, (_, k) => vars[k] ?? "");
}
async function act(page, step, selector, vars) {
  const value = interpolate3(step.value, vars);
  switch (step.action) {
    case "navigate":
      await page.goto(interpolate3(step.value, vars) || page.url());
      return;
    case "wait":
      await page.waitForTimeout(Number(value) || 500);
      return;
  }
  if (!selector)
    throw new Error(`action ${step.action} requires a resolved selector`);
  const locator = page.locator(selector).first();
  switch (step.action) {
    case "click":
      await locator.click();
      return;
    case "type":
      await locator.fill(value);
      return;
    case "select":
      await locator.selectOption(value);
      return;
    case "keypress":
      await locator.press(value);
      return;
    case "submit":
      await locator.press("Enter");
      return;
  }
}

// src/grounding/dom-extractor.ts
function extractInteractiveElementsInPage() {
  const INTERACTIVE_SELECTOR = "button,a,input,select,textarea,[role=button],[role=link],[role=textbox],[role=checkbox],[role=radio],[role=menuitem],[role=tab],[tabindex],[onclick]";
  const els = Array.from(
    document.querySelectorAll(INTERACTIVE_SELECTOR)
  );
  const accessibleName = (el) => {
    const ariaLabel = el.getAttribute("aria-label");
    if (ariaLabel) return ariaLabel;
    const labelledBy = el.getAttribute("aria-labelledby");
    if (labelledBy) {
      const target = document.getElementById(labelledBy);
      if (target?.textContent) return target.textContent.trim();
    }
    if (el.id) {
      const forLabel = document.querySelector(`label[for="${el.id}"]`);
      if (forLabel?.textContent) return forLabel.textContent.trim();
    }
    const placeholder = el.getAttribute("placeholder");
    if (placeholder) return placeholder;
    const title = el.getAttribute("title");
    if (title) return title;
    const text2 = el.textContent?.trim();
    return text2 || void 0;
  };
  const xpathFor = (el) => {
    if (el.id) return `//*[@id="${el.id}"]`;
    const parts = [];
    let node = el;
    while (node && node.nodeType === Node.ELEMENT_NODE) {
      let index = 1;
      let sibling = node.previousElementSibling;
      while (sibling) {
        if (sibling.tagName === node.tagName) index++;
        sibling = sibling.previousElementSibling;
      }
      parts.unshift(`${node.tagName.toLowerCase()}[${index}]`);
      node = node.parentElement;
    }
    return `/${parts.join("/")}`;
  };
  const contextPathFor = (el) => {
    const path4 = [];
    let node = el.parentElement;
    let depth = 0;
    while (node && depth < 5) {
      path4.push(node.tagName.toLowerCase() + (node.id ? `#${node.id}` : ""));
      node = node.parentElement;
      depth++;
    }
    return path4;
  };
  const regionFor = (el) => {
    if (el.closest('[role="dialog"], .modal, dialog')) return "modal";
    if (el.closest("form")) return "form";
    if (el.closest("section")) return "section";
    return null;
  };
  const cssSelectorFor = (el) => {
    if (el.id) return `#${el.id}`;
    const testId = el.getAttribute("data-testid");
    if (testId) return `[data-testid="${testId}"]`;
    const tag = el.tagName.toLowerCase();
    const type = el.getAttribute("type");
    if (tag === "input" && type) return `input[type='${type}']`;
    return xpathFor(el);
  };
  return els.map((el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    const visible = style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    const siblings = Array.from(el.parentElement?.children ?? []).filter(
      (s) => s.tagName === el.tagName
    );
    const attributes = {};
    for (const attr of Array.from(el.attributes))
      attributes[attr.name] = attr.value;
    return {
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute("role") ?? void 0,
      label: accessibleName(el),
      disabled: el.disabled === true || el.getAttribute("aria-disabled") === "true",
      visible,
      focusable: el.tabIndex >= 0,
      clickable: true,
      boundingBox: {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height
      },
      ancestorChain: contextPathFor(el),
      region: regionFor(el),
      nearbyText: el.parentElement?.textContent?.trim().slice(0, 200),
      testId: el.getAttribute("data-testid") ?? void 0,
      attributes,
      xpath: xpathFor(el),
      contextPath: contextPathFor(el),
      siblingIndex: siblings.indexOf(el),
      cssSelector: cssSelectorFor(el)
    };
  });
}

// src/grounding/candidate.ts
async function extractCandidates(page) {
  const raw = await page.evaluate(extractInteractiveElementsInPage);
  return raw.map((r, i) => ({
    id: `cand_${i}`,
    selector: r.cssSelector,
    tag: r.tag,
    role: r.role,
    label: r.label,
    disabled: r.disabled,
    visible: r.visible,
    focusable: r.focusable,
    clickable: r.clickable,
    boundingBox: r.boundingBox,
    ancestorChain: r.ancestorChain,
    region: r.region,
    nearbyText: r.nearbyText,
    testId: r.testId,
    attributes: r.attributes,
    xpath: r.xpath,
    contextPath: r.contextPath,
    siblingIndex: r.siblingIndex
  }));
}

// src/grounding/dom-hash.ts
import { createHash } from "crypto";
function computeDomHash(candidates) {
  const signature = candidates.map(
    (c) => `${c.tag}|${c.role ?? ""}|${c.testId ?? ""}|${c.attributes?.id ?? ""}`
  ).sort().join(";");
  return createHash("sha256").update(signature).digest("hex");
}

// src/execution/locate.ts
async function isUniqueVisible(locator) {
  const count = await locator.count();
  if (count !== 1) return false;
  return locator.isVisible().catch(() => false);
}
async function locate(test, step, page, cache, healing) {
  const domCandidates = await extractCandidates(page);
  const domHash = computeDomHash(domCandidates);
  const testId = test.flow.id;
  const hit = cache.getSelector(testId, step.id, domHash);
  if (hit && await isUniqueVisible(page.locator(hit.cachedSelector))) {
    return { locator: page.locator(hit.cachedSelector), source: "cached" };
  }
  const seed = step.target?.resolution?.cachedSelector;
  if (seed && await isUniqueVisible(page.locator(seed))) {
    cache.putSelector({
      testId,
      stepId: step.id,
      domHash,
      cachedSelector: seed,
      band: step.target.resolution.band
    });
    return { locator: page.locator(seed), source: "cached" };
  }
  const outcome = await healing.runtimeHeal(test, step.id, page, seed ?? null);
  if (outcome.status === "healed") {
    return {
      locator: page.locator(outcome.cachedSelector),
      source: "resolver"
    };
  }
  return { locator: null, source: "none" };
}

// src/execution/types.ts
function checkPrecondition(step, page) {
  for (const p of step.preconditions) {
    if (p.kind === "url_contains" && !page.url().includes(p.value))
      return Promise.resolve(false);
  }
  return Promise.resolve(true);
}

// src/execution/adapters/ui.ts
var UiAdapter = class {
  kind = "ui";
  async execute(step, ctx) {
    const start = Date.now();
    if (!await checkPrecondition(step, ctx.page)) {
      return fail(step.id, "STATE_BLOCKED", "precondition not met", start);
    }
    const isTarget = step.action !== "navigate" && step.action !== "wait";
    let selection = void 0;
    let band = void 0;
    if (isTarget) {
      const groundedStep = ctx.test.steps.find((s) => s.id === step.id);
      if (groundedStep?.kind !== "ui")
        return fail(
          step.id,
          "NOT_GROUNDED",
          "step is not a grounded ui step",
          start
        );
      const result = await locate(
        ctx.test,
        groundedStep,
        ctx.page,
        ctx.cache,
        ctx.healing
      );
      selection = result.source;
      if (!result.locator) {
        return {
          stepId: step.id,
          status: "stale",
          selection: "none",
          durationMs: Date.now() - start
        };
      }
      band = groundedStep.target?.resolution?.band;
    }
    const urlBefore = ctx.page.url();
    try {
      const groundedStep = ctx.test.steps.find((s) => s.id === step.id);
      const cachedSelector = groundedStep?.kind === "ui" ? groundedStep.target?.resolution?.cachedSelector ?? null : null;
      await act(ctx.page, step, isTarget ? cachedSelector : null, ctx.vars);
    } catch (e) {
      return maybeInvert(
        step,
        fail(step.id, "ACTION_FAILED", String(e), start),
        selection,
        band
      );
    }
    for (const outcome of step.expectedOutcome) {
      const res = await evaluateExpectedOutcome(outcome, {
        page: ctx.page,
        urlBefore,
        vars: ctx.vars
      });
      if (!res.ok)
        return maybeInvert(
          step,
          fail(
            step.id,
            "EXPECTED_OUTCOME_FAILED",
            res.reason ?? "",
            start,
            selection,
            band
          ),
          selection,
          band
        );
    }
    for (const a of step.assertions) {
      const res = await evaluateAssertion(a, {
        page: ctx.page,
        vars: ctx.vars
      });
      if (!res.ok)
        return maybeInvert(
          step,
          fail(
            step.id,
            "ASSERTION_FAILED",
            res.reason ?? "",
            start,
            selection,
            band
          ),
          selection,
          band
        );
    }
    const passed = {
      stepId: step.id,
      status: "passed",
      selection,
      band,
      durationMs: Date.now() - start
    };
    return maybeInvert(step, passed, selection, band);
  }
};
function fail(stepId, reason, message, start, selection, band) {
  return {
    stepId,
    status: "failed",
    selection,
    band,
    failure: { reason, message },
    durationMs: Date.now() - start
  };
}
function maybeInvert(step, result, selection, band) {
  if (!step.negative) return result;
  if (result.status === "passed")
    return {
      ...result,
      status: "failed",
      failure: {
        reason: "NEGATIVE_TEST",
        message: "app accepted input it should have rejected"
      }
    };
  if (result.status === "failed")
    return {
      stepId: step.id,
      status: "passed",
      selection,
      band,
      durationMs: result.durationMs
    };
  return result;
}

// src/execution/playwright.ts
import {
  chromium,
  firefox,
  webkit
} from "playwright";
var ENGINES = { chromium, firefox, webkit };
async function openSession(config2) {
  const browser = await ENGINES[config2.browser].launch({
    headless: config2.headless
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  page.setDefaultTimeout(config2.timeouts.actionMs);
  page.setDefaultNavigationTimeout(config2.timeouts.navMs);
  return {
    browser,
    context,
    page,
    close: async () => {
      await context.close();
      await browser.close();
    }
  };
}

// src/execution/verdict.ts
function aggregate(runId, test, results, startedAt) {
  const executed = results.filter((r) => r.status !== "skipped");
  const hasFailed = results.some(
    (r) => r.status === "failed" || r.status === "stale"
  );
  const needsReview = results.some((r) => r.status === "stale");
  return {
    runId,
    testId: test.flow.id,
    status: !hasFailed && executed.length > 0 ? "passed" : "failed",
    needsReview,
    steps: results,
    startedAt,
    finishedAt: (/* @__PURE__ */ new Date()).toISOString()
  };
}

// src/execution/dispatcher.ts
function isFatal(onFailure, result) {
  return result.status === "failed" && onFailure === "abort";
}
var PlaywrightTestRunner = class {
  constructor(config2, cache, healing) {
    this.config = config2;
    this.cache = cache;
    this.healing = healing;
  }
  config;
  cache;
  healing;
  adapters = {
    ui: new UiAdapter(),
    api: new ApiAdapter(),
    db: new DbAdapter()
  };
  async run(test, opts) {
    const runId = opts.runId ?? randomUUID2();
    const startedAt = (/* @__PURE__ */ new Date()).toISOString();
    const session = await openSession(this.config);
    const ctx = {
      test,
      page: session.page,
      vars: { ...test.flow.vars, ...opts.vars ?? {} },
      cache: this.cache,
      healing: this.healing
    };
    const results = [];
    opts.emit?.({ type: "run.start", runId, testId: test.flow.id });
    try {
      await session.page.goto(test.groundedUrl);
      for (const step of test.steps) {
        opts.emit?.({ type: "step.start", stepId: step.id });
        let result = await this.adapters[step.kind].execute(step, ctx);
        if (result.status === "failed" && step.onFailure === "retry_once") {
          result = await this.adapters[step.kind].execute(step, ctx);
        }
        if (result.status === "failed" && step.onFailure === "optional")
          result = { ...result, status: "warning" };
        results.push(result);
        opts.emit?.({ type: "step.result", result });
        if (isFatal(step.onFailure, result)) break;
      }
    } finally {
      await session.close();
    }
    const report = aggregate(runId, test, results, startedAt);
    this.cache.saveRun(report);
    opts.emit?.({ type: "run.complete", report });
    return report;
  }
};

// src/grounding/emitter.ts
function mergeResolution(step, resolution) {
  if (step.kind !== "ui") return step;
  if (!step.target) return { ...step, target: void 0 };
  return { ...step, target: { ...step.target, resolution } };
}
function toGroundedTest(spec, steps, groundedUrl) {
  return {
    ...spec,
    groundedAt: (/* @__PURE__ */ new Date()).toISOString(),
    groundedUrl,
    steps
  };
}

// src/grounding/gate.ts
function accept(band) {
  return band !== "low";
}
function durableSelector(winner) {
  if (winner.anchors.testId) return `[data-testid="${winner.anchors.testId}"]`;
  if (winner.anchors.attributes?.id) return `#${winner.anchors.attributes.id}`;
  return winner.selector;
}
function withCachedSelector(resolution) {
  const winner = resolution.candidates.find((c) => c.id === resolution.selected) ?? null;
  return {
    status: resolution.status,
    confidence: resolution.confidence,
    band: resolution.band,
    selected: resolution.selected,
    cachedSelector: winner ? durableSelector(winner) : null,
    winner
  };
}
function toWinnerOnly(resolution) {
  return {
    ...withCachedSelector(resolution),
    status: "ungrounded",
    selected: null,
    cachedSelector: null,
    winner: null
  };
}

// src/resolver/router.ts
var BASE_WEIGHTS = {
  semantics: 0.45,
  context: 0.33,
  structure: 0.22
};
function computeWeights(page, allScores) {
  const w = { ...BASE_WEIGHTS };
  if (page.iconRatio > 0.5) w.structure += 0.15;
  if (page.textDensity > 0.6) w.semantics += 0.1;
  if (page.hasForm || page.hasModal) w.context += 0.1;
  for (const key of Object.keys(w)) {
    const allZero = allScores.every((s) => s[key] === 0);
    if (allZero) w[key] = 0;
  }
  const total = w.semantics + w.context + w.structure;
  if (total === 0) return { semantics: 0, context: 0, structure: 0 };
  return {
    semantics: w.semantics / total,
    context: w.context / total,
    structure: w.structure / total
  };
}
function finalScore(scores, weights) {
  return scores.semantics * weights.semantics + scores.context * weights.context + scores.structure * weights.structure;
}
function characterizePage(candidates) {
  const withText = candidates.filter(
    (c) => c.label && c.label.trim().length > 0
  ).length;
  const iconLike = candidates.filter(
    (c) => !c.label || c.label.trim().length === 0
  ).length;
  return {
    textDensity: candidates.length ? withText / candidates.length : 0,
    iconRatio: candidates.length ? iconLike / candidates.length : 0,
    hasForm: candidates.some((c) => c.region === "form"),
    hasModal: candidates.some((c) => c.region === "modal"),
    repeatedStructure: new Set(candidates.map((c) => c.tag)).size < candidates.length / 2
  };
}

// src/grounding/normalize.ts
function normalize(target, candidates, generalization) {
  return {
    target,
    candidates,
    page: characterizePage(candidates),
    generalization
  };
}

// src/grounding/index.ts
function isNonTargetStep(step) {
  return step.kind === "ui" && (step.action === "navigate" || step.action === "wait");
}
var PlaywrightGroundingService = class {
  constructor(resolver, config2) {
    this.resolver = resolver;
    this.config = config2;
  }
  resolver;
  config;
  async ground(spec, opts) {
    const vars = { ...spec.flow.vars, ...opts.vars ?? {} };
    const session = await openSession(this.config);
    const candidatesDoc = {
      version: "1.0",
      specId: spec.flow.id,
      groundedAt: (/* @__PURE__ */ new Date()).toISOString(),
      groundedUrl: spec.flow.startUrl,
      steps: []
    };
    const groundedSteps = [];
    let stoppedAt;
    try {
      await session.page.goto(spec.flow.startUrl);
      for (const step of spec.steps) {
        if (step.kind !== "ui" || isNonTargetStep(step)) {
          if (step.kind === "ui") await act(session.page, step, null, vars);
          groundedSteps.push(step);
          continue;
        }
        if (!step.target) {
          groundedSteps.push(step);
          continue;
        }
        const domCandidates = await extractCandidates(session.page);
        const input = normalize(
          step.target,
          domCandidates,
          step.generalization
        );
        const resolution = await this.resolver.resolve(input);
        candidatesDoc.steps.push({ stepId: step.id, resolution });
        if (accept(resolution.band)) {
          const grounded = withCachedSelector(resolution);
          groundedSteps.push(mergeResolution(step, grounded));
          await act(session.page, step, grounded.cachedSelector, vars);
        } else {
          groundedSteps.push(mergeResolution(step, toWinnerOnly(resolution)));
          stoppedAt = step.id;
          break;
        }
      }
    } finally {
      await session.close();
    }
    return {
      candidates: candidatesDoc,
      grounded: toGroundedTest(spec, groundedSteps, spec.flow.startUrl),
      stoppedAt
    };
  }
  // Single-step re-ground for runtime heal (LLD-006). Reuses the caller's live page — no new browser.
  async reground(test, stepId, page) {
    const step = test.steps.find((s) => s.id === stepId);
    if (!step || step.kind !== "ui" || !step.target) {
      throw new Error(`step ${stepId} is not a groundable UI step`);
    }
    const domCandidates = await extractCandidates(page);
    const domHash = computeDomHash(domCandidates);
    const input = normalize(step.target, domCandidates, step.generalization);
    const resolution = await this.resolver.resolve(input);
    const winner = resolution.candidates.find(
      (c) => c.id === resolution.selected
    );
    const cachedSelector = accept(resolution.band) && winner ? durableSelector(winner) : null;
    return { band: resolution.band, cachedSelector, resolution, domHash };
  }
};

// src/healing/audit.ts
function audit(cache, testId, stepId, event, opts) {
  cache.appendHeal({
    testId,
    stepId,
    event,
    fromSel: opts.from ?? null,
    toSel: opts.to ?? null,
    band: opts.band,
    reason: opts.reason,
    at: (/* @__PURE__ */ new Date()).toISOString()
  });
}

// src/healing/review.ts
function enqueue(cache, testId, stepId, url, topCandidates) {
  cache.enqueueReview({
    testId,
    stepId,
    url,
    candidatesJson: JSON.stringify(topCandidates)
  });
}

// src/healing/runtime.ts
async function runtimeHeal(grounding, cache, test, stepId, page, previousSelector) {
  const result = await grounding.reground(test, stepId, page);
  if (result.band !== "low" && result.cachedSelector) {
    cache.putSelector({
      testId: test.flow.id,
      stepId,
      domHash: result.domHash,
      cachedSelector: result.cachedSelector,
      band: result.band
    });
    audit(cache, test.flow.id, stepId, "healed", {
      from: previousSelector,
      to: result.cachedSelector,
      band: result.band
    });
    return {
      status: "healed",
      cachedSelector: result.cachedSelector,
      band: result.band,
      from: previousSelector
    };
  }
  const topCandidates = result.resolution.candidates.slice(0, 5);
  enqueue(cache, test.flow.id, stepId, page.url(), topCandidates);
  audit(cache, test.flow.id, stepId, "stale", {
    from: previousSelector,
    reason: "no candidate reached medium confidence"
  });
  return {
    status: "stale",
    reason: "no candidate reached medium confidence",
    topCandidates
  };
}

// src/healing/repair.ts
async function buildRepairPayload(store, testId) {
  const specIR = await store.loadSpec(testId);
  const testCase = await store.loadGrounded(testId);
  return { specIR, testCase, kdg: null };
}
async function maintain(authoring, grounding, store, testId, _stepIds, patchedSpec) {
  const before = await store.loadGrounded(testId);
  const spec = await authoring.submit(patchedSpec);
  const outcome = await grounding.ground(spec, {});
  return { testId, before, after: outcome.grounded };
}

// src/healing/index.ts
var CoreHealingService = class {
  constructor(grounding, cache, authoring, store) {
    this.grounding = grounding;
    this.cache = cache;
    this.authoring = authoring;
    this.store = store;
  }
  grounding;
  cache;
  authoring;
  store;
  runtimeHeal(test, stepId, page, previousSelector) {
    return runtimeHeal(this.grounding, this.cache, test, stepId, page, previousSelector);
  }
  buildRepairPayload(testId) {
    return buildRepairPayload(this.store, testId);
  }
  maintain(testId, stepIds, patchedSpec) {
    return maintain(this.authoring, this.grounding, this.store, testId, stepIds, patchedSpec);
  }
};

// src/resolver/embeddings.ts
import { createHash as createHash2 } from "crypto";
var TransformersEmbeddingModel = class {
  constructor(modelId) {
    this.modelId = modelId;
  }
  modelId;
  pipe = null;
  async load() {
    if (this.pipe) return this.pipe;
    const { pipeline } = await import("@huggingface/transformers");
    this.pipe = await pipeline("feature-extraction", this.modelId);
    return this.pipe;
  }
  async embed(text2) {
    const pipe = await this.load();
    const out = await pipe(text2, { pooling: "mean", normalize: true });
    return out.data;
  }
};
function embeddingCacheKey(model, text2) {
  return createHash2("sha256").update(`${model}:${text2}`).digest("hex");
}
function cosineSimilarity(a, b) {
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
var CachedEmbedder = class {
  constructor(model, modelId, cache) {
    this.model = model;
    this.modelId = modelId;
    this.cache = cache;
  }
  model;
  modelId;
  cache;
  async embed(text2) {
    const key = embeddingCacheKey(this.modelId, text2);
    const cached = this.cache.getEmbedding(key);
    if (cached) return cached;
    const vector = await this.model.embed(text2);
    this.cache.putEmbedding(key, this.modelId, vector);
    return vector;
  }
};

// src/resolver/banding.ts
var CONFIDENCE_MARGIN = 0.15;
function toBand(score, bands) {
  if (score >= bands.high) return "high";
  if (score >= bands.medium) return "medium";
  return "low";
}
function selectBest(scored, generalization, bands) {
  if (scored.length === 0)
    return { winner: null, band: "low", ambiguous: false };
  const sorted = [...scored].sort((a, b) => b.score - a.score);
  const top = sorted[0];
  const runnerUp = sorted[1];
  const requiresMargin = generalization === "same_element" || generalization === "any_matching";
  const margin = generalization === "same_element" ? CONFIDENCE_MARGIN : CONFIDENCE_MARGIN / 2;
  let band = toBand(top.score, bands);
  let ambiguous = false;
  if (requiresMargin && runnerUp && top.score - runnerUp.score < margin) {
    const tiebreakWinner = tiebreak(
      sorted.filter((s) => top.score - s.score < margin)
    );
    if (tiebreakWinner) {
      return {
        winner: tiebreakWinner,
        band: toBand(tiebreakWinner.score, bands),
        ambiguous: false
      };
    }
    ambiguous = true;
    band = band === "high" ? "medium" : "low";
  }
  return { winner: top, band, ambiguous };
}
function tiebreak(tied) {
  const withTestId = tied.find((s) => s.candidate.testId);
  if (withTestId) return withTestId;
  const withSiblingIndex = [...tied].sort(
    (a, b) => (a.candidate.siblingIndex ?? 99) - (b.candidate.siblingIndex ?? 99)
  );
  if (withSiblingIndex[0]?.candidate.siblingIndex !== void 0)
    return withSiblingIndex[0];
  return null;
}

// src/resolver/signals/affordance.ts
var ACTION_TAGS = {
  type: ["input", "textarea"],
  select: ["select"],
  click: ["button", "a", "input", "select", "textarea"],
  focus: ["input", "textarea", "select", "button", "a"],
  keypress: ["input", "textarea"]
};
var AffordanceSignal = class {
  name = "affordance";
  score(target, cand, _ctx) {
    if (cand.visible === false || cand.disabled === true) return 0;
    for (const action of target.actions) {
      const allowedTags = ACTION_TAGS[action];
      if (!allowedTags) continue;
      const roleOk = cand.role ? allowedTags.includes(cand.role) : false;
      const tagOk = allowedTags.includes(cand.tag);
      if (!roleOk && !tagOk) return 0;
    }
    return 1;
  }
};

// src/resolver/signals/context.ts
function jaccard(a, b) {
  const setA = new Set(a.toLowerCase().split(/\s+/).filter(Boolean));
  const setB = new Set(b.toLowerCase().split(/\s+/).filter(Boolean));
  if (setA.size === 0 || setB.size === 0) return 0;
  let inter = 0;
  for (const w of setA) if (setB.has(w)) inter++;
  const union = setA.size + setB.size - inter;
  return union === 0 ? 0 : inter / union;
}
var ContextSignal = class {
  name = "context";
  score(target, cand, ctx) {
    let score = 0.5;
    if (ctx.hasForm && cand.region === "form") score += 0.2;
    if (ctx.hasModal && cand.region === "modal") score += 0.2;
    if (cand.nearbyText) {
      const textMatch = Math.max(
        jaccard(cand.nearbyText, target.label),
        jaccard(cand.nearbyText, target.intent)
      );
      score += textMatch * 0.3;
    }
    return Math.min(1, score);
  }
};

// src/resolver/signals/index-signal.ts
var IndexSignal = class {
  name = "index";
  score(_target, cand, _ctx) {
    return cand.siblingIndex !== void 0 ? 0.5 : 0;
  }
};

// src/resolver/signals/semantics.ts
var SemanticsSignal = class {
  constructor(embedder) {
    this.embedder = embedder;
  }
  embedder;
  name = "semantics";
  async score(target, cand, _ctx) {
    const candText = cand.label?.trim();
    if (!candText) return 0;
    const targetTexts = [...target.semantics, target.label];
    const candVec = await this.embedder.embed(candText);
    let best = -1;
    for (const t of targetTexts) {
      const vec = await this.embedder.embed(t);
      best = Math.max(best, cosineSimilarity(vec, candVec));
    }
    return Math.min(1, Math.max(0, (best + 1) / 2));
  }
};

// src/resolver/signals/structure.ts
var ROLE_SYNONYMS = {
  button: ["button", "submit"],
  textbox: ["textbox", "input"],
  link: ["link", "a"]
};
var StructureSignal = class {
  name = "structure";
  score(target, cand, _ctx) {
    if (cand.testId) return 1;
    let score = 0;
    if (cand.attributes?.id) score += 0.3;
    const wantRole = target.role.toLowerCase();
    const gotRole = cand.role?.toLowerCase();
    if (gotRole === wantRole) score += 0.4;
    else if (ROLE_SYNONYMS[wantRole]?.includes(gotRole ?? "")) score += 0.3;
    else if (ROLE_SYNONYMS[wantRole]?.includes(cand.tag)) score += 0.2;
    if (cand.xpath) score += 0.15;
    if (cand.contextPath && cand.contextPath.length > 0) score += 0.15;
    return Math.min(1, score);
  }
};

// src/resolver/index.ts
var MultiSignalResolver = class {
  constructor(embedder, bands) {
    this.bands = bands;
    this.semantics = new SemanticsSignal(embedder);
  }
  bands;
  affordance = new AffordanceSignal();
  context = new ContextSignal();
  structure = new StructureSignal();
  index = new IndexSignal();
  semantics;
  async resolve(input) {
    const { target, candidates, page, generalization } = input;
    const survivors = candidates.filter(
      (c) => this.affordance.score(target, c, page) === 1
    );
    if (survivors.length === 0) {
      return {
        status: "ungrounded",
        confidence: 0,
        band: "low",
        selected: null,
        cachedSelector: null,
        candidates: []
      };
    }
    const rawScores = [];
    const semanticsScores = [];
    const contextScores = [];
    const structureScores = [];
    const indexScores = [];
    for (const c of survivors) {
      const [sem, ctx, struct] = await Promise.all([
        this.semantics.score(target, c, page),
        Promise.resolve(this.context.score(target, c, page)),
        Promise.resolve(this.structure.score(target, c, page))
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
      score: finalScore(rawScores[i], weights)
    }));
    const { winner, band, ambiguous } = selectBest(
      scored,
      generalization,
      this.bands
    );
    const candidatesOut = survivors.map((c, i) => ({
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
        nearbyText: c.nearbyText
      },
      signals: {
        semantics: semanticsScores[i],
        affordance: 1,
        context: contextScores[i],
        structure: structureScores[i],
        index: indexScores[i]
      },
      score: scored[i].score,
      band: scored[i].score >= this.bands.high ? "high" : scored[i].score >= this.bands.medium ? "medium" : "low"
    }));
    candidatesOut.sort((a, b) => b.score - a.score);
    if (!winner || ambiguous) {
      return {
        status: "ungrounded",
        confidence: winner?.score ?? 0,
        band,
        selected: null,
        cachedSelector: null,
        candidates: candidatesOut
      };
    }
    return {
      status: band === "low" ? "ungrounded" : "grounded",
      confidence: winner.score,
      band,
      selected: winner.candidate.id,
      cachedSelector: null,
      // grounding's gate.ts fills this in from the winner's anchors
      candidates: candidatesOut
    };
  }
};

// src/storage/index.ts
import { randomUUID as randomUUID3 } from "crypto";
import fs3 from "fs/promises";
import { CandidatesDoc, GroundedTest, SpecIR as SpecIR2 } from "@axiom/shared";

// src/storage/layout.ts
import path3 from "path";
function testDir(artifactsDir, testId) {
  return path3.join(artifactsDir, testId);
}
function specPath(artifactsDir, testId) {
  return path3.join(testDir(artifactsDir, testId), "spec.json");
}
function candidatesPath(artifactsDir, testId) {
  return path3.join(testDir(artifactsDir, testId), "candidates.json");
}
function groundedPath(artifactsDir, testId) {
  return path3.join(testDir(artifactsDir, testId), "grounded.json");
}

// src/storage/index.ts
var FsArtifactStore = class {
  constructor(artifactsDir) {
    this.artifactsDir = artifactsDir;
  }
  artifactsDir;
  async saveSpec(spec, testId = randomUUID3()) {
    const validated = SpecIR2.parse(spec);
    await fs3.mkdir(testDir(this.artifactsDir, testId), { recursive: true });
    await fs3.writeFile(
      specPath(this.artifactsDir, testId),
      JSON.stringify(validated, null, 2)
    );
    return testId;
  }
  async saveGrounded(testId, test) {
    const validated = GroundedTest.parse(test);
    await fs3.mkdir(testDir(this.artifactsDir, testId), { recursive: true });
    await fs3.writeFile(
      groundedPath(this.artifactsDir, testId),
      JSON.stringify(validated, null, 2)
    );
  }
  async saveCandidates(testId, doc) {
    const validated = CandidatesDoc.parse(doc);
    await fs3.mkdir(testDir(this.artifactsDir, testId), { recursive: true });
    await fs3.writeFile(
      candidatesPath(this.artifactsDir, testId),
      JSON.stringify(validated, null, 2)
    );
  }
  async loadSpec(testId) {
    const raw = await fs3.readFile(specPath(this.artifactsDir, testId), "utf-8");
    return SpecIR2.parse(JSON.parse(raw));
  }
  async loadGrounded(testId) {
    const raw = await fs3.readFile(
      groundedPath(this.artifactsDir, testId),
      "utf-8"
    );
    return GroundedTest.parse(JSON.parse(raw));
  }
  async list() {
    await fs3.mkdir(this.artifactsDir, { recursive: true });
    const ids = await fs3.readdir(this.artifactsDir);
    const out = [];
    for (const testId of ids) {
      try {
        const spec = await this.loadSpec(testId);
        const grounded = await fs3.access(groundedPath(this.artifactsDir, testId)).then(() => true).catch(() => false);
        out.push({ testId, name: spec.flow.name, grounded });
      } catch {
      }
    }
    return out;
  }
  async delete(testId) {
    await fs3.rm(testDir(this.artifactsDir, testId), {
      recursive: true,
      force: true
    });
  }
};

// src/server/container.ts
function buildContainer(config2) {
  const db = openDb(config2.dbPath);
  migrate(db);
  const cache = new SqliteCacheStore(db);
  const embedder = new CachedEmbedder(
    new TransformersEmbeddingModel(config2.embeddingModel),
    config2.embeddingModel,
    cache
  );
  const resolver = new MultiSignalResolver(embedder, config2.bands);
  const store = new FsArtifactStore(config2.artifactsDir);
  const grounding = new PlaywrightGroundingService(resolver, config2);
  const kdg = new EmptyKdgContextProvider();
  const authoring = new CoreAuthoringService(kdg);
  const healing = new CoreHealingService(grounding, cache, authoring, store);
  const runner = new PlaywrightTestRunner(config2, cache, healing);
  return {
    config: config2,
    cache,
    store,
    resolver,
    grounding,
    authoring,
    healing,
    runner,
    kdg
  };
}

// src/server/main.ts
var config = loadConfig();
var container = buildContainer(config);
var app = await buildApp(config, container);
app.listen({ port: config.port, host: "127.0.0.1" }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});
//# sourceMappingURL=main.js.map