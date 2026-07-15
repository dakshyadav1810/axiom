import type { Command } from "commander";
import open from "open";
import { CoreClient } from "./client.js";
import { baseUrl, loadConfig } from "./config.js";
import { startCore, stopCore } from "./core-process.js";
import { startMcp } from "./mcp/server.js";

export function registerCommands(program: Command) {
  program
    .command("init")
    .description("scaffold .axiom/ + axiom.config.json in the project")
    .action(async () => {
      const fs = await import("node:fs");
      fs.mkdirSync(".axiom/tests", { recursive: true });
      if (!fs.existsSync("axiom.config.json")) {
        fs.writeFileSync(
          "axiom.config.json",
          JSON.stringify({ port: 4319 }, null, 2),
        );
      }
      console.log("initialized .axiom/ and axiom.config.json");
    });

  program
    .command("start")
    .description("spawn core, start MCP (stdio), open dashboard")
    .action(async () => {
      const config = loadConfig();
      const coreEntry = await resolveCoreEntry();
      await startCore(config, coreEntry);
      console.log(`core listening on ${baseUrl(config)}`);
      await open(baseUrl(config));
      const client = new CoreClient(baseUrl(config));
      await startMcp(client); // blocks on stdio
    });

  program
    .command("stop")
    .description("graceful shutdown of core")
    .action(() => {
      console.log(
        stopCore()
          ? "core stopped"
          : "no running core found (.axiom/axiom.pid missing)",
      );
    });

  // No `axiom author` command: Axiom has no LLM client. A spec can only be created by a connected
  // agent calling `submitSpec` over MCP (SPEC-001 §2).

  program
    .command("ground")
    .argument("<testId>")
    .description("first-run grounding")
    .action(async (testId) => {
      const client = new CoreClient(baseUrl(loadConfig()));
      console.log(JSON.stringify(await client.groundTest(testId), null, 2));
    });

  program
    .command("test")
    .argument("[testId]")
    .description("run test / suite; print report")
    .action(async (testId) => {
      const client = new CoreClient(baseUrl(loadConfig()));
      const ids = testId
        ? [testId]
        : (await client.listTests()).map((t) => t.testId);
      let allPassed = true;
      for (const id of ids) {
        const { runId } = await client.runTest({ testId: id });
        const report = await pollReport(client, runId);
        console.log(
          `${id}: ${report.status}${report.needsReview ? " (needs review)" : ""}`,
        );
        if (report.status !== "passed") allPassed = false;
      }
      process.exitCode = allPassed ? 0 : 1;
    });

  program
    .command("heal")
    .argument("<testId>")
    .description("print the repair payload for a stale test (read-only — no LLM call)")
    .action(async (testId) => {
      const client = new CoreClient(baseUrl(loadConfig()));
      const payload = await client.getRepairPayload(testId);
      console.log(JSON.stringify(payload, null, 2));
      console.log(
        "\nHand this to your connected coding agent, then have it call `updateTest` (or `axiom heal` " +
          "again after it submits a fix) — Axiom has no LLM of its own to repair this automatically.",
      );
    });

  program
    .command("report")
    .argument("<runId>")
    .description("print a stored run report")
    .action(async (runId) => {
      const client = new CoreClient(baseUrl(loadConfig()));
      console.log(JSON.stringify(await client.getReport(runId), null, 2));
    });
}

async function pollReport(client: CoreClient, runId: string) {
  for (let i = 0; i < 200; i++) {
    try {
      return await client.getReport(runId);
    } catch {
      await new Promise((r) => setTimeout(r, 300));
    }
  }
  throw new Error(`run ${runId} did not complete in time`);
}

// Resolves core's file path only, to hand to execa as a child process — never imported/called
// directly (invariant #7). @axiom/core is a dependency solely so this path resolves once published.
async function resolveCoreEntry(): Promise<string> {
  const { createRequire } = await import("node:module");
  return createRequire(import.meta.url).resolve("@axiom/core");
}
