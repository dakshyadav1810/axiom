// KDG data structure deferred (ADR-002 out-of-scope). This is the v1 empty-context default (LLD-002 §6):
// authoring proceeds from intent alone when no KDG is available.
export interface KdgContext {
  routes: { path: string; forms: { label: string; role: string }[] }[];
  conditionals: unknown[];
}

export interface KdgContextProvider {
  build(entryUrl: string): Promise<KdgContext>;
}

export class EmptyKdgContextProvider implements KdgContextProvider {
  async build(_entryUrl: string): Promise<KdgContext> {
    return { routes: [], conditionals: [] };
  }
}
