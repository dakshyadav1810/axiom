import { randomUUID } from "node:crypto";
import { MaintainRequest, RunRequest } from "@axiom/shared";
import type { FastifyInstance } from "fastify";
import type { Container } from "./container.js";
import type { WsHub } from "./ws-hub.js";

function apiError(code: string, message: string) {
  return { error: { code, message } };
}

export async function registerRoutes(
  app: FastifyInstance,
  c: Container,
  hub: WsHub,
) {
  app.get("/health", async () => ({ ok: true, version: "0.1.0" }));

  // --- tests ---
  // The only way a spec is created: the connected agent has already authored it and submits the
  // finished SpecIR here. Core validates + stores; it never generates one itself.
  app.post("/tests", async (req, reply) => {
    try {
      const spec = await c.authoring.submit(req.body);
      const testId = await c.store.saveSpec(spec);
      return { testId, spec };
    } catch (e) {
      reply.code(400);
      return apiError("validation", String(e));
    }
  });

  app.get("/tests", async () => c.store.list());

  app.get("/tests/:id", async (req, reply) => {
    const { id } = req.params as { id: string };
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

  app.delete("/tests/:id", async (req) => {
    const { id } = req.params as { id: string };
    await c.store.delete(id);
    return { ok: true };
  });

  app.post("/tests/:id/ground", async (req, reply) => {
    const { id } = req.params as { id: string };
    const spec = await c.store.loadSpec(id);
    const outcome = await c.grounding.ground(spec, {});
    await c.store.saveCandidates(id, outcome.candidates);
    await c.store.saveGrounded(id, outcome.grounded);
    if (outcome.stoppedAt) reply.code(200); // still 200: partial grounding is a valid, reviewable result
    return outcome;
  });

  app.get("/tests/:id/repair", async (req) => {
    const { id } = req.params as { id: string };
    return c.healing.buildRepairPayload(id);
  });

  app.post("/tests/:id/maintain", async (req) => {
    const { id } = req.params as { id: string };
    const { stepIds, spec } = MaintainRequest.parse(req.body);
    const result = await c.healing.maintain(id, stepIds, spec);
    await c.store.saveGrounded(id, result.after);
    return result;
  });

  // --- runs ---
  app.post("/runs", async (req) => {
    const { testId, vars } = RunRequest.parse(req.body);
    const test = await c.store.loadGrounded(testId);
    const runId = randomUUID();
    // fire-and-forget: client polls GET /runs/:id or streams GET /ws/runs/:id (LLD-008 §3-4)
    c.runner
      .run(test, { vars, runId, emit: (m) => hub.emit(`run:${runId}`, m) })
      .catch((e) => req.log.error(e));
    return { runId };
  });

  app.get("/runs/:id", async (req, reply) => {
    const { id } = req.params as { id: string };
    const report = c.cache.getRun(id);
    if (!report) {
      reply.code(404);
      return apiError("not_found", `run ${id} not found`);
    }
    return report;
  });

  // --- kdg ---
  app.get("/kdg", async (req) => {
    const { entry } = req.query as { entry?: string };
    return c.kdg.build(entry ?? "");
  });
  app.get("/kdg/delta", async () => ({ changed: [] })); // future — needs KDG versioning (SPEC-005)
}
