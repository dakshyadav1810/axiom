import type { Tier1Target } from "@axiom/shared";
import type { DomCandidate, PageContext, SignalStrategy } from "../base.js";

const ACTION_TAGS: Record<string, string[]> = {
  type: ["input", "textarea"],
  select: ["select"],
  click: ["button", "a", "input", "select", "textarea"],
  focus: ["input", "textarea", "select", "button", "a"],
  keypress: ["input", "textarea"],
};

// "can it perform this action?" — hard filter, not a scored dimension (LLD-004 §3, §5; DECISIONS.md #7)
export class AffordanceSignal implements SignalStrategy {
  readonly name = "affordance" as const;

  score(target: Tier1Target, cand: DomCandidate, _ctx: PageContext): number {
    if (cand.visible === false || cand.disabled === true) return 0;
    for (const action of target.actions) {
      const allowedTags = ACTION_TAGS[action];
      if (!allowedTags) continue;
      const roleOk = cand.role ? allowedTags.includes(cand.role) : false;
      const tagOk = allowedTags.includes(cand.tag);
      if (!roleOk && !tagOk) return 0;
    }
    return 1;
  }
}
