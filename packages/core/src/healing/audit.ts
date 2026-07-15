import type { Band } from "@axiom/shared";
import type { CacheStore } from "../cache/index.js";

export function audit(
  cache: CacheStore,
  testId: string,
  stepId: string,
  event: "healed" | "stale",
  opts: {
    from?: string | null;
    to?: string | null;
    band?: Band;
    reason?: string;
  },
): void {
  cache.appendHeal({
    testId,
    stepId,
    event,
    fromSel: opts.from ?? null,
    toSel: opts.to ?? null,
    band: opts.band,
    reason: opts.reason,
    at: new Date().toISOString(),
  });
}
