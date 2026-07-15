import type { GroundedTest, Step, StepKind, StepResult } from "@axiom/shared";
import type { Page } from "playwright";
import type { CacheStore } from "../cache/index.js";
import type { HealingService } from "../healing/index.js";

export interface RunContext {
  test: GroundedTest;
  page: Page;
  vars: Record<string, string>;
  cache: CacheStore;
  healing: HealingService;
  dbQuery?: (query: string) => Promise<unknown>;
}

export interface StepAdapter {
  readonly kind: StepKind;
  execute(step: Step, ctx: RunContext): Promise<StepResult>;
}

export function checkPrecondition(step: Step, page: Page): Promise<boolean> {
  // Minimal, synchronous-enough checks; full visibility/enabled checks apply to UI targets during locate.
  for (const p of step.preconditions) {
    if (p.kind === "url_contains" && !page.url().includes(p.value))
      return Promise.resolve(false);
  }
  return Promise.resolve(true);
}
