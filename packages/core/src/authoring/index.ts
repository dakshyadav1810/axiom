import { lintSpec, SpecIR } from "@axiom/shared";
import type { KdgContext, KdgContextProvider } from "./kdg-context.js";
import { normalizeLlmOutput } from "./emitter.js";

export interface AuthoringService {
  /** The only way a spec is created: an agent has already authored it; core validates + stores. */
  submit(spec: unknown): Promise<SpecIR>;
  /** Context an authoring agent should read (also exposed as the MCP getMap tool). */
  context(entryUrl: string): Promise<KdgContext>;
}

export class AuthoringError extends Error {}

// No LLM client here, ever — Axiom never calls a model provider. The connected agent (Claude Code,
// Cursor, ...) authors the spec entirely in its own session and hands core the finished SpecIR.
export class CoreAuthoringService implements AuthoringService {
  constructor(private kdg: KdgContextProvider) {}

  async context(entryUrl: string): Promise<KdgContext> {
    return this.kdg.build(entryUrl);
  }

  async submit(spec: unknown): Promise<SpecIR> {
    const parsed = SpecIR.parse(normalizeLlmOutput(spec));
    const lint = lintSpec(parsed);
    if (!lint.ok) throw new AuthoringError(`spec failed lint: ${lint.errors.join("; ")}`);
    return parsed;
  }
}
