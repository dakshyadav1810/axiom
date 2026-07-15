import type { Tier1Target } from "@axiom/shared";
import type { DomCandidate, PageContext, SignalStrategy } from "../base.js";

const ROLE_SYNONYMS: Record<string, string[]> = {
  button: ["button", "submit"],
  textbox: ["textbox", "input"],
  link: ["link", "a"],
};

// "can we identify it by what it is?" — structural identity, formerly "selector" (LLD-004 §3)
export class StructureSignal implements SignalStrategy {
  readonly name = "structure" as const;

  score(target: Tier1Target, cand: DomCandidate, _ctx: PageContext): number {
    if (cand.testId) return 1; // data-testid is the strongest structural anchor

    let score = 0;
    if (cand.attributes?.id) score += 0.3;

    const wantRole = target.role.toLowerCase();
    const gotRole = cand.role?.toLowerCase();
    if (gotRole === wantRole) score += 0.4;
    else if (ROLE_SYNONYMS[wantRole]?.includes(gotRole ?? "")) score += 0.3;
    else if (ROLE_SYNONYMS[wantRole]?.includes(cand.tag)) score += 0.2;

    if (cand.xpath) score += 0.15;
    if (cand.contextPath && cand.contextPath.length > 0) score += 0.15;

    return Math.min(1, score);
  }
}
