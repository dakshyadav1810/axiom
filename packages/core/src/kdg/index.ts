// Thin per LLD-000 §3 — KDG data structure deferred (ADR-002). Contract lives in authoring/kdg-context.ts.
export type {
  KdgContext,
  KdgContextProvider,
} from "../authoring/kdg-context.js";
export { EmptyKdgContextProvider } from "../authoring/kdg-context.js";
