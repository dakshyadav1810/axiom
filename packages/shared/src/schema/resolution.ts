import { z } from "zod";
import { Candidate } from "./candidates.js";
import { Band, ResolutionStatus, Score } from "./enums.js";

// resolver's verdict for one target — full ranked list (LLD-001 §5)
export const Resolution = z.object({
  status: ResolutionStatus,
  confidence: Score,
  band: Band,
  selected: z.string().nullable(),
  cachedSelector: z.string().nullable(),
  candidates: z.array(Candidate), // ranked, best first
});
export type Resolution = z.infer<typeof Resolution>;

// grounded artifact stores the WINNER only, not the full ranking (see groundedTest.ts)
export const GroundedResolution = Resolution.omit({ candidates: true }).extend({
  winner: Candidate.nullable(),
});
export type GroundedResolution = z.infer<typeof GroundedResolution>;

// candidates.json — grounding's raw per-step output (full ranking, pre-merge)
export const CandidatesDoc = z.object({
  version: z.literal("1.0"),
  specId: z.string(),
  groundedAt: z.string(),
  groundedUrl: z.string().url(),
  steps: z.array(
    z.object({
      stepId: z.string(),
      resolution: Resolution,
    }),
  ),
});
export type CandidatesDoc = z.infer<typeof CandidatesDoc>;
