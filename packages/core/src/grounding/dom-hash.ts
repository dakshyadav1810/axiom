import { createHash } from "node:crypto";
import type { DomCandidate } from "../resolver/base.js";

// Stable hash of the page's interactive-DOM signature (LLD-007 §4). Computed identically at
// grounding and at run time so a materially changed page misses the selector cache.
export function computeDomHash(candidates: DomCandidate[]): string {
  const signature = candidates
    .map(
      (c) =>
        `${c.tag}|${c.role ?? ""}|${c.testId ?? ""}|${c.attributes?.id ?? ""}`,
    )
    .sort()
    .join(";");
  return createHash("sha256").update(signature).digest("hex");
}
