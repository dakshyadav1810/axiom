import { z } from "zod";
import { Band, Score } from "./enums.js";

export const BoundingBox = z.object({
  x: z.number(),
  y: z.number(),
  width: z.number(),
  height: z.number(),
});
export type BoundingBox = z.infer<typeof BoundingBox>;

export const SignalScores = z.object({
  semantics: Score,
  affordance: Score,
  context: Score,
  structure: Score,
  index: Score,
});
export type SignalScores = z.infer<typeof SignalScores>;

// one considered DOM element (grounding-captured, persisted subset) — LLD-001 §5
export const Candidate = z.object({
  id: z.string(),
  selector: z.string(),
  label: z.string().optional(),
  role: z.string().optional(),
  boundingBox: BoundingBox.optional(),
  anchors: z
    .object({
      testId: z.string().optional(),
      attributes: z.record(z.string()).default({}),
      xpath: z.string().optional(),
      contextPath: z.array(z.string()).default([]),
      siblingIndex: z.number().optional(),
      nearbyText: z.string().optional(),
    })
    .partial()
    .default({}),
  signals: SignalScores,
  score: Score,
  band: Band,
});
export type Candidate = z.infer<typeof Candidate>;
