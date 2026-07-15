# LLD-002: Authoring Service (`core/authoring`)

**Status:** Draft
**Implements:** [SPEC-001](../specs/SPEC-001-authoring.md), [ADR-002 §1](../adr/ADR-002.md)
**Depends on:** [LLD-001](./LLD-001-shared-ir.md) (SpecIR), [LLD-008](./LLD-008-mcp-server.md) (MCP)

> Axiom holds no LLM provider client, no API key, and no prompt-building logic. The connected agent
> (Claude Code, Cursor, ...) is the LLM — it authors the spec entirely in its own session and hands core
> a finished `SpecIR`. Core's only job is to supply KDG context, then validate and store what comes back.

---

## 1. Module shape

```
core/src/authoring/
├── index.ts              # AuthoringService (public interface)
├── kdg-context.ts        # KdgContextProvider — assembles authoring context (getMap)
├── emitter.ts             # normalize + validate agent-submitted spec → SpecIR
└── store.ts              # persist/read spec.json via storage (LLD-007)
```

There is no `llm-client.ts` and no `prompt.ts` — nothing in this module ever calls out to a model
provider. If a future version needs one, that's a new, explicit decision, not an implicit default.

## 2. Interface

```ts
export interface AuthoringService {
  /** The only way a spec is created: an agent has already authored it; core validates + stores. */
  submit(spec: unknown): Promise<SpecIR>;
  /** Context an authoring agent should read (also exposed as the MCP getMap tool). */
  context(entryUrl: string): Promise<KdgContext>;
}

export interface KdgContextProvider {
  build(entryUrl: string): Promise<KdgContext>;   // routes, forms, conditionals, parent/child
}
```

`KdgContext` is the versioned app-structure summary the agent reads (see `core/kdg` — data structure
deferred; the *contract* is: routes/pages, per-page forms & controls with roles/labels, conditionals,
and parent/child containment). Absent a KDG, `context()` returns an empty context and the agent authors
from intent alone.

## 3. `submit()` algorithm

```ts
async submit(raw) {
  const parsed = SpecIR.safeParse(this.emitter.normalize(raw));
  if (!parsed.success) throw new AuthoringError(parsed.error.issues.map(i => i.message).join("; "));
  const lint = lintSpec(parsed.data);
  if (!lint.ok) throw new AuthoringError(lint.errors.join("; "));
  return this.store.save(parsed.data);           // status: authored/ungrounded
}
```

- **No retry loop lives here.** If validation fails, the error is returned to the caller (the agent); any
  retry with a corrected spec happens in the agent's own session, not inside core.
- `emitter.normalize` repairs only trivial drift (snake/camel casing, missing defaults) before parsing —
  it does not and cannot fix semantic mistakes, because it has no model to reason with.

## 4. Lint rules (beyond schema)

- every `${var}` in any step/assertion exists in `flow.vars`;
- each UI step with an actuating `action` has a `target`; `wait`/`navigate` have none;
- at least one assertion or `expectedOutcome` across the spec (no assertion-free tests);
- `semantics[]` non-empty and not just the role word; `role` is a known ARIA/implicit role.

## 5. Determinism & boundaries

- `submit()` is deterministic: same input spec, same validation result. Whatever nondeterminism produced
  the spec's content happened upstream, in the agent's own model call — outside this module and outside
  Axiom's process entirely.
- Authoring **never** sees the live DOM and **never** emits selectors (that's grounding, LLD-003).
- It writes only `spec.json` via `storage` (LLD-007); it does not run tests.
- **No provider key exists anywhere in Axiom's config.** There is nothing to hold (invariant #6 is
  satisfied trivially — there's no secret to leak because there's no provider client).

## 6. Maintenance reuses this exact path

The maintenance-heal flow (LLD-006 §6) does not add a second, provider-calling code path here. It builds
a `RepairPayload` for the agent to read, and when the agent submits its fix, that call lands on this same
`submit()` — a repair is just a resubmission of a (partially) new `SpecIR`.
