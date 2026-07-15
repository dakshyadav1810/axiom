import { z } from "zod";

// DOM-blind — what the LLM authors (LLD-001 §2).
export const Tier1Target = z.object({
  label: z.string(),
  semantics: z.array(z.string()).min(1),
  role: z.string(),
  actions: z.array(z.string()).default([]),
  intent: z.string(),
});
export type Tier1Target = z.infer<typeof Tier1Target>;
