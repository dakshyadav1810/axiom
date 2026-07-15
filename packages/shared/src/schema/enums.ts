import { z } from "zod";

export const ActionType = z.enum([
  "navigate",
  "click",
  "type",
  "select",
  "keypress",
  "submit",
  "wait",
]);
export type ActionType = z.infer<typeof ActionType>;

export const StepKind = z.enum(["ui", "api", "db"]);
export type StepKind = z.infer<typeof StepKind>;

export const Generalization = z.enum([
  "same_element",
  "any_matching",
  "aggressive",
  "flexible",
]);
export type Generalization = z.infer<typeof Generalization>;

export const OnFailure = z.enum([
  "abort",
  "continue",
  "retry_once",
  "optional",
]);
export type OnFailure = z.infer<typeof OnFailure>;

export const SignalName = z.enum([
  "semantics",
  "affordance",
  "context",
  "structure",
  "index",
]);
export type SignalName = z.infer<typeof SignalName>;

export const Band = z.enum(["high", "medium", "low"]);
export type Band = z.infer<typeof Band>;

export const ResolutionStatus = z.enum(["grounded", "ungrounded", "stale"]);
export type ResolutionStatus = z.infer<typeof ResolutionStatus>;

export const Score = z.number().min(0).max(1);
export type Score = z.infer<typeof Score>;
