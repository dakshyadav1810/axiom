#!/usr/bin/env node

// src/index.ts
import { Command } from "commander";

// src/commands.ts
import open from "open";

// src/client.ts
var CoreClient = class {
  constructor(base) {
    this.base = base;
  }
  base;
  async req(method, path2, body) {
    const res = await fetch(`${this.base}${path2}`, {
      method,
      headers: body ? { "content-type": "application/json" } : void 0,
      body: body ? JSON.stringify(body) : void 0
    });
    if (!res.ok)
      throw new Error(
        `${method} ${path2} -> ${res.status}: ${await res.text()}`
      );
    return res.json();
  }
  health() {
    return this.req("GET", "/health");
  }
  getKdg(entryUrl) {
    return this.req(
      "GET",
      `/kdg?entry=${encodeURIComponent(entryUrl)}`
    );
  }
  submitSpec(spec) {
    return this.req("POST", "/tests", spec);
  }
  groundTest(testId) {
    return this.req(
      "POST",
      `/tests/${testId}/ground`
    );
  }
  listTests() {
    return this.req("GET", "/tests");
  }
  getTest(testId) {
    return this.req("GET", `/tests/${testId}`);
  }
  deleteTest(testId) {
    return this.req("DELETE", `/tests/${testId}`);
  }
  runTest(req) {
    return this.req("POST", "/runs", req);
  }
  getReport(runId) {
    return this.req("GET", `/runs/${runId}`);
  }
  getRepairPayload(testId) {
    return this.req("GET", `/tests/${testId}/repair`);
  }
  maintain(testId, req) {
    return this.req(
      "POST",
      `/tests/${testId}/maintain`,
      req
    );
  }
};

// src/config.ts
import fs from "fs";
import { AxiomConfig } from "@axiom/shared";
function loadConfig(flags = {}) {
  let fileConfig = {};
  try {
    fileConfig = JSON.parse(fs.readFileSync("axiom.config.json", "utf-8"));
  } catch {
  }
  const envConfig = process.env.AXIOM_PORT ? { port: Number(process.env.AXIOM_PORT) } : {};
  return AxiomConfig.parse({ ...fileConfig, ...envConfig, ...flags });
}
function baseUrl(config) {
  return `http://127.0.0.1:${config.port}`;
}

// src/core-process.ts
import fs2 from "fs";
import path from "path";
import { execa } from "execa";
var PID_FILE = path.join(".axiom", "axiom.pid");
async function waitForHealth(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${url}/health`);
      if (res.ok) return;
    } catch {
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error(`core did not become healthy within ${timeoutMs}ms`);
}
async function startCore(config, coreEntry) {
  const child = execa("node", [coreEntry], {
    env: { ...process.env, AXIOM_PORT: String(config.port) },
    detached: true,
    stdio: "ignore"
  });
  fs2.mkdirSync(".axiom", { recursive: true });
  fs2.writeFileSync(PID_FILE, String(child.pid));
  child.unref();
  await waitForHealth(baseUrl(config), 15e3);
  return child;
}
function stopCore() {
  if (!fs2.existsSync(PID_FILE)) return false;
  const pid = Number(fs2.readFileSync(PID_FILE, "utf-8"));
  try {
    process.kill(pid, "SIGTERM");
  } catch {
  }
  fs2.rmSync(PID_FILE, { force: true });
  return true;
}

// src/mcp/server.ts
import { RunRequest, SpecIR } from "@axiom/shared";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
function buildMcpServer(client) {
  const server = new McpServer({ name: "axiom", version: "0.1.0" });
  server.tool("getMap", { entryUrl: z.string() }, async ({ entryUrl }) => {
    const kdg = await client.getKdg(entryUrl);
    return { content: [{ type: "text", text: JSON.stringify(kdg) }] };
  });
  server.tool("getDelta", { sinceVersion: z.string() }, async () => ({
    content: [{ type: "text", text: JSON.stringify({ changed: [] }) }]
  }));
  server.tool("submitSpec", SpecIR.shape, async (spec) => {
    const res = await client.submitSpec(spec);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });
  server.tool("groundTest", { testId: z.string() }, async ({ testId }) => {
    const res = await client.groundTest(testId);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });
  server.tool("runTest", RunRequest.shape, async (req) => {
    const res = await client.runTest(req);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });
  server.tool("getReport", { runId: z.string() }, async ({ runId }) => {
    const res = await client.getReport(runId);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });
  server.tool("pollRun", { runId: z.string() }, async ({ runId }) => {
    const res = await client.getReport(runId);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });
  server.tool("healing", { testId: z.string() }, async ({ testId }) => {
    const res = await client.getRepairPayload(testId);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });
  server.tool(
    "updateTest",
    {
      testId: z.string(),
      stepIds: z.array(z.string()),
      spec: SpecIR
    },
    async ({ testId, stepIds, spec }) => {
      const res = await client.maintain(testId, { stepIds, spec });
      return { content: [{ type: "text", text: JSON.stringify(res) }] };
    }
  );
  server.tool("deleteTest", { testId: z.string() }, async ({ testId }) => {
    const res = await client.deleteTest(testId);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });
  return server;
}
async function startMcp(client) {
  const server = buildMcpServer(client);
  await server.connect(new StdioServerTransport());
}

// src/commands.ts
function registerCommands(program2) {
  program2.command("init").description("scaffold .axiom/ + axiom.config.json in the project").action(async () => {
    const fs3 = await import("fs");
    fs3.mkdirSync(".axiom/tests", { recursive: true });
    if (!fs3.existsSync("axiom.config.json")) {
      fs3.writeFileSync(
        "axiom.config.json",
        JSON.stringify({ port: 4319 }, null, 2)
      );
    }
    console.log("initialized .axiom/ and axiom.config.json");
  });
  program2.command("start").description("spawn core, start MCP (stdio), open dashboard").action(async () => {
    const config = loadConfig();
    const coreEntry = await resolveCoreEntry();
    await startCore(config, coreEntry);
    console.log(`core listening on ${baseUrl(config)}`);
    await open(baseUrl(config));
    const client = new CoreClient(baseUrl(config));
    await startMcp(client);
  });
  program2.command("stop").description("graceful shutdown of core").action(() => {
    console.log(
      stopCore() ? "core stopped" : "no running core found (.axiom/axiom.pid missing)"
    );
  });
  program2.command("ground").argument("<testId>").description("first-run grounding").action(async (testId) => {
    const client = new CoreClient(baseUrl(loadConfig()));
    console.log(JSON.stringify(await client.groundTest(testId), null, 2));
  });
  program2.command("test").argument("[testId]").description("run test / suite; print report").action(async (testId) => {
    const client = new CoreClient(baseUrl(loadConfig()));
    const ids = testId ? [testId] : (await client.listTests()).map((t) => t.testId);
    let allPassed = true;
    for (const id of ids) {
      const { runId } = await client.runTest({ testId: id });
      const report = await pollReport(client, runId);
      console.log(
        `${id}: ${report.status}${report.needsReview ? " (needs review)" : ""}`
      );
      if (report.status !== "passed") allPassed = false;
    }
    process.exitCode = allPassed ? 0 : 1;
  });
  program2.command("heal").argument("<testId>").description("print the repair payload for a stale test (read-only \u2014 no LLM call)").action(async (testId) => {
    const client = new CoreClient(baseUrl(loadConfig()));
    const payload = await client.getRepairPayload(testId);
    console.log(JSON.stringify(payload, null, 2));
    console.log(
      "\nHand this to your connected coding agent, then have it call `updateTest` (or `axiom heal` again after it submits a fix) \u2014 Axiom has no LLM of its own to repair this automatically."
    );
  });
  program2.command("report").argument("<runId>").description("print a stored run report").action(async (runId) => {
    const client = new CoreClient(baseUrl(loadConfig()));
    console.log(JSON.stringify(await client.getReport(runId), null, 2));
  });
}
async function pollReport(client, runId) {
  for (let i = 0; i < 200; i++) {
    try {
      return await client.getReport(runId);
    } catch {
      await new Promise((r) => setTimeout(r, 300));
    }
  }
  throw new Error(`run ${runId} did not complete in time`);
}
async function resolveCoreEntry() {
  const { createRequire } = await import("module");
  return createRequire(import.meta.url).resolve("@axiom/core");
}

// src/index.ts
var program = new Command("axiom").description(
  "Axiom \u2014 deterministic-first AI-native testing platform"
);
registerCommands(program);
program.parseAsync(process.argv);
//# sourceMappingURL=index.js.map