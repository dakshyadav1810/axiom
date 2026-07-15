import { z } from "zod";
import { RunReport, StepResult } from "./dto.js";
import { Band } from "./enums.js";

export const WsMessage = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("run.start"),
    runId: z.string(),
    testId: z.string(),
  }),
  z.object({ type: z.literal("step.start"), stepId: z.string() }),
  z.object({
    type: z.literal("resolver.event"),
    stepId: z.string(),
    band: Band,
    selected: z.string().nullable(),
  }),
  z.object({ type: z.literal("step.result"), result: StepResult }),
  z.object({
    type: z.literal("log"),
    level: z.enum(["info", "warn", "error"]),
    line: z.string(),
  }),
  z.object({ type: z.literal("run.complete"), report: RunReport }),
]);
export type WsMessage = z.infer<typeof WsMessage>;
