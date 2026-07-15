import { z } from "zod";
import { ActionType, Generalization, OnFailure, StepKind } from "./enums.js";
import { Tier1Target } from "./target.js";

export const Precondition = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("visible") }),
  z.object({ kind: z.literal("enabled") }),
  z.object({ kind: z.literal("modal_open") }),
  z.object({ kind: z.literal("url_contains"), value: z.string() }),
]);
export type Precondition = z.infer<typeof Precondition>;

export const ExpectedOutcome = z.discriminatedUnion("type", [
  z.object({ type: z.literal("navigation") }),
  z.object({ type: z.literal("url_change"), value: z.string() }),
  z.object({ type: z.literal("element_appears"), value: z.string() }),
  z.object({ type: z.literal("text_contains"), value: z.string() }),
  z.object({ type: z.literal("field_contains"), value: z.string() }),
]);
export type ExpectedOutcome = z.infer<typeof ExpectedOutcome>;

export const Assertion = z.discriminatedUnion("type", [
  z.object({ type: z.literal("urlContains"), expected: z.string() }),
  z.object({ type: z.literal("textContains"), expected: z.string() }),
  z.object({ type: z.literal("value"), expected: z.string() }),
  z.object({ type: z.literal("elementVisible"), target: Tier1Target }),
  z.object({ type: z.literal("elementAbsent"), target: Tier1Target }),
  z.object({ type: z.literal("apiStatus"), expected: z.number() }),
  z.object({
    type: z.literal("apiBody"),
    path: z.string(),
    expected: z.unknown(),
  }),
  z.object({
    type: z.literal("dbRow"),
    query: z.string(),
    expected: z.unknown(),
  }),
]);
export type Assertion = z.infer<typeof Assertion>;

const StepBase = z.object({
  id: z.string(),
  intent: z.string(),
  onFailure: OnFailure.default("abort"),
  preconditions: z.array(Precondition).default([]),
  assertions: z.array(Assertion).default([]),
  // negative test: app SHOULD reject; runtime inverts the verdict (SPEC-003 §6)
  negative: z.boolean().default(false),
});

export const UiStep = StepBase.extend({
  kind: z.literal("ui"),
  action: ActionType,
  value: z.string().optional(),
  generalization: Generalization.default("same_element"),
  expectedOutcome: z.array(ExpectedOutcome).default([]),
  target: Tier1Target.optional(), // omitted for wait/navigate
});
export type UiStep = z.infer<typeof UiStep>;

export const ApiStep = StepBase.extend({
  kind: z.literal("api"),
  request: z.object({
    method: z.enum(["GET", "POST", "PUT", "PATCH", "DELETE"]),
    url: z.string(),
    headers: z.record(z.string()).optional(),
    body: z.unknown().optional(),
  }),
});
export type ApiStep = z.infer<typeof ApiStep>;

export const DbStep = StepBase.extend({
  kind: z.literal("db"),
  query: z.string(),
});
export type DbStep = z.infer<typeof DbStep>;

export const Step = z.discriminatedUnion("kind", [UiStep, ApiStep, DbStep]);
export type Step = z.infer<typeof Step>;
