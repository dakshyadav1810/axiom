import type { Page } from "playwright";
import type { GroundedTest, RepairPayload, SpecIR } from "@axiom/shared";
import type { AuthoringService } from "../authoring/index.js";
import type { CacheStore } from "../cache/index.js";
import type { GroundingService } from "../grounding/index.js";
import type { ArtifactStore } from "../storage/index.js";
import { type HealOutcome, runtimeHeal } from "./runtime.js";
import { buildRepairPayload, maintain, type RepairResult } from "./repair.js";

export type { HealOutcome } from "./runtime.js";
export type { RepairResult } from "./repair.js";

export interface HealingService {
  runtimeHeal(test: GroundedTest, stepId: string, page: Page, previousSelector: string | null): Promise<HealOutcome>;
  buildRepairPayload(testId: string): Promise<RepairPayload>;
  /** patchedSpec is required — the agent always supplies the fix. No provider fallback. */
  maintain(testId: string, stepIds: string[], patchedSpec: SpecIR): Promise<RepairResult>;
}

export class CoreHealingService implements HealingService {
  constructor(
    private grounding: GroundingService,
    private cache: CacheStore,
    private authoring: AuthoringService,
    private store: ArtifactStore,
  ) {}

  runtimeHeal(test: GroundedTest, stepId: string, page: Page, previousSelector: string | null): Promise<HealOutcome> {
    return runtimeHeal(this.grounding, this.cache, test, stepId, page, previousSelector);
  }

  buildRepairPayload(testId: string): Promise<RepairPayload> {
    return buildRepairPayload(this.store, testId);
  }

  maintain(testId: string, stepIds: string[], patchedSpec: SpecIR): Promise<RepairResult> {
    return maintain(this.authoring, this.grounding, this.store, testId, stepIds, patchedSpec);
  }
}
