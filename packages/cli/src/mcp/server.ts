import { RunRequest, SpecIR } from "@axiom/shared";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import type { CoreClient } from "../client.js";

// Agent-facing MCP control plane, hosted by `axiom start`. Every tool proxies to core over REST —
// no in-process shortcut (invariant #7, LLD-008).
export function buildMcpServer(client: CoreClient): McpServer {
  const server = new McpServer({ name: "axiom", version: "0.1.0" });

  server.tool("getMap", { entryUrl: z.string() }, async ({ entryUrl }) => {
    const kdg = await client.getKdg(entryUrl);
    return { content: [{ type: "text", text: JSON.stringify(kdg) }] };
  });

  server.tool("getDelta", { sinceVersion: z.string() }, async () => ({
    content: [{ type: "text", text: JSON.stringify({ changed: [] }) }],
  }));

  // The only way a spec is created — the agent authors it in its own session and submits the result.
  server.tool("submitSpec", SpecIR.shape, async (spec) => {
    const res = await client.submitSpec(spec as SpecIR);
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

  // spec is required: the agent reads `healing` for context, re-authors the fix itself, and submits it
  // here. There is no core-side repair fallback.
  server.tool(
    "updateTest",
    {
      testId: z.string(),
      stepIds: z.array(z.string()),
      spec: SpecIR,
    },
    async ({ testId, stepIds, spec }) => {
      const res = await client.maintain(testId, { stepIds, spec });
      return { content: [{ type: "text", text: JSON.stringify(res) }] };
    },
  );

  server.tool("deleteTest", { testId: z.string() }, async ({ testId }) => {
    const res = await client.deleteTest(testId);
    return { content: [{ type: "text", text: JSON.stringify(res) }] };
  });

  return server;
}

export async function startMcp(client: CoreClient) {
  const server = buildMcpServer(client);
  await server.connect(new StdioServerTransport());
}
