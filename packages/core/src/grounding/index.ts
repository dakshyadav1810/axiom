import type {
  AxiomConfig,
  Band,
  CandidatesDoc,
  GroundedStep,
  GroundedTest,
  Resolution,
  SpecIR,
} from "@axiom/shared";
import type { Page } from "playwright";
import { act } from "../execution/act.js";
import { openSession } from "../execution/playwright.js";
import type { Resolver } from "../resolver/index.js";
import { extractCandidates } from "./candidate.js";
import { computeDomHash } from "./dom-hash.js";
import { mergeResolution, toGroundedTest } from "./emitter.js";
import {
  accept,
  durableSelector,
  toWinnerOnly,
  withCachedSelector,
} from "./gate.js";
import { normalize } from "./normalize.js";

export interface GroundingOutcome {
  candidates: CandidatesDoc;
  grounded: GroundedTest;
  stoppedAt?: string;
}

export interface StepResolution {
  band: Band;
  cachedSelector: string | null;
  resolution: Resolution; // full ranked list — healing needs it for review records
  domHash: string;
}

export interface GroundingService {
  ground(
    spec: SpecIR,
    opts: { vars?: Record<string, string> },
  ): Promise<GroundingOutcome>;
  reground(
    test: GroundedTest,
    stepId: string,
    page: Page,
  ): Promise<StepResolution>;
}

function isNonTargetStep(step: SpecIR["steps"][number]): boolean {
  return (
    step.kind === "ui" && (step.action === "navigate" || step.action === "wait")
  );
}

export class PlaywrightGroundingService implements GroundingService {
  constructor(
    private resolver: Resolver,
    private config: AxiomConfig,
  ) {}

  async ground(
    spec: SpecIR,
    opts: { vars?: Record<string, string> },
  ): Promise<GroundingOutcome> {
    const vars = { ...spec.flow.vars, ...(opts.vars ?? {}) };
    const session = await openSession(this.config);
    const candidatesDoc: CandidatesDoc = {
      version: "1.0",
      specId: spec.flow.id,
      groundedAt: new Date().toISOString(),
      groundedUrl: spec.flow.startUrl,
      steps: [],
    };
    const groundedSteps: GroundedStep[] = [];
    let stoppedAt: string | undefined;

    try {
      await session.page.goto(spec.flow.startUrl);

      for (const step of spec.steps) {
        if (step.kind !== "ui" || isNonTargetStep(step)) {
          if (step.kind === "ui") await act(session.page, step, null, vars);
          groundedSteps.push(step);
          continue;
        }
        if (!step.target) {
          groundedSteps.push(step);
          continue;
        }

        const domCandidates = await extractCandidates(session.page);
        const input = normalize(
          step.target,
          domCandidates,
          step.generalization,
        );
        const resolution = await this.resolver.resolve(input);
        candidatesDoc.steps.push({ stepId: step.id, resolution });

        if (accept(resolution.band)) {
          const grounded = withCachedSelector(resolution);
          groundedSteps.push(mergeResolution(step, grounded));
          await act(session.page, step, grounded.cachedSelector, vars); // ACT-to-advance
        } else {
          groundedSteps.push(mergeResolution(step, toWinnerOnly(resolution)));
          stoppedAt = step.id;
          break;
        }
      }
    } finally {
      await session.close();
    }

    return {
      candidates: candidatesDoc,
      grounded: toGroundedTest(spec, groundedSteps, spec.flow.startUrl),
      stoppedAt,
    };
  }

  // Single-step re-ground for runtime heal (LLD-006). Reuses the caller's live page — no new browser.
  async reground(
    test: GroundedTest,
    stepId: string,
    page: Page,
  ): Promise<StepResolution> {
    const step = test.steps.find((s) => s.id === stepId);
    if (!step || step.kind !== "ui" || !step.target) {
      throw new Error(`step ${stepId} is not a groundable UI step`);
    }
    const domCandidates = await extractCandidates(page);
    const domHash = computeDomHash(domCandidates);
    const input = normalize(step.target, domCandidates, step.generalization);
    const resolution = await this.resolver.resolve(input);
    const winner = resolution.candidates.find(
      (c) => c.id === resolution.selected,
    );
    const cachedSelector =
      accept(resolution.band) && winner ? durableSelector(winner) : null;
    return { band: resolution.band, cachedSelector, resolution, domHash };
  }
}
