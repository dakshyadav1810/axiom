import type { Generalization, SignalName, Tier1Target } from "@axiom/shared";

// Raw element extracted live from the page — pre-scoring (grounding's dom-extractor produces these).
export interface DomCandidate {
  id: string;
  selector: string;
  tag: string;
  role?: string;
  label?: string; // accessible name: visible text / aria-label / placeholder / label-for / title
  disabled?: boolean;
  visible?: boolean;
  focusable?: boolean;
  clickable?: boolean;
  boundingBox?: { x: number; y: number; width: number; height: number };
  ancestorChain?: string[]; // up to 5, nearest first
  region?: "form" | "modal" | "section" | null;
  nearbyText?: string;
  testId?: string;
  attributes?: Record<string, string>;
  xpath?: string;
  contextPath?: string[];
  siblingIndex?: number;
}

export interface PageContext {
  textDensity: number; // 0..1
  iconRatio: number; // 0..1
  hasForm: boolean;
  hasModal: boolean;
  repeatedStructure: boolean;
}

export type ResolverInput = {
  target: Tier1Target;
  candidates: DomCandidate[];
  page: PageContext;
  generalization: Generalization;
};

export interface SignalStrategy {
  readonly name: SignalName;
  // 0..1 (affordance: 0/1). Semantics needs the embedding cache/model, hence the Promise.
  score(
    target: Tier1Target,
    cand: DomCandidate,
    ctx: PageContext,
  ): number | Promise<number>;
}
