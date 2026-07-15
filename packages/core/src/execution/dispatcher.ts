import { randomUUID } from "node:crypto";
import type {
  AxiomConfig,
  GroundedTest,
  RunReport,
  StepResult,
  WsMessage,
} from "@axiom/shared";
import type { CacheStore } from "../cache/index.js";
import type { HealingService } from "../healing/index.js";
import { ApiAdapter } from "./adapters/api.js";
import { DbAdapter } from "./adapters/db.js";
import { UiAdapter } from "./adapters/ui.js";
import { openSession } from "./playwright.js";
import type { RunContext, StepAdapter } from "./types.js";
import { aggregate } from "./verdict.js";

export interface TestRunner {
  run(
    test: GroundedTest,
    opts: {
      vars?: Record<string, string>;
      emit?: (m: WsMessage) => void;
      runId?: string;
    },
  ): Promise<RunReport>;
}

function isFatal(onFailure: string, result: StepResult): boolean {
  return result.status === "failed" && onFailure === "abort";
}

export class PlaywrightTestRunner implements TestRunner {
  private adapters: Record<string, StepAdapter> = {
    ui: new UiAdapter(),
    api: new ApiAdapter(),
    db: new DbAdapter(),
  };

  constructor(
    private config: AxiomConfig,
    private cache: CacheStore,
    private healing: HealingService,
  ) {}

  async run(
    test: GroundedTest,
    opts: {
      vars?: Record<string, string>;
      emit?: (m: WsMessage) => void;
      runId?: string;
    },
  ): Promise<RunReport> {
    const runId = opts.runId ?? randomUUID();
    const startedAt = new Date().toISOString();
    const session = await openSession(this.config);
    const ctx: RunContext = {
      test,
      page: session.page,
      vars: { ...test.flow.vars, ...(opts.vars ?? {}) },
      cache: this.cache,
      healing: this.healing,
    };
    const results: StepResult[] = [];

    opts.emit?.({ type: "run.start", runId, testId: test.flow.id });
    try {
      await session.page.goto(test.groundedUrl);
      for (const step of test.steps) {
        opts.emit?.({ type: "step.start", stepId: step.id });
        let result = await this.adapters[step.kind].execute(step, ctx);
        if (result.status === "failed" && step.onFailure === "retry_once") {
          result = await this.adapters[step.kind].execute(step, ctx);
        }
        if (result.status === "failed" && step.onFailure === "optional")
          result = { ...result, status: "warning" };
        results.push(result);
        opts.emit?.({ type: "step.result", result });
        if (isFatal(step.onFailure, result)) break;
      }
    } finally {
      await session.close();
    }

    const report = aggregate(runId, test, results, startedAt);
    this.cache.saveRun(report);
    opts.emit?.({ type: "run.complete", report });
    return report;
  }
}
